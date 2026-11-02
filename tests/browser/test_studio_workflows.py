"""P8 profile, draft, fault and multi-tab workflows using real native storage and transport."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import socket
import tempfile

from playwright.sync_api import Error, expect, sync_playwright
from test_customization_studio import document
from test_profile_publication import PIN, launch, stop
from companion.profile_contracts import encode_document

FAULTS = """(() => {
  window.studioFault = {quota:false, deletion:false, cleanup:false};
  const put = IDBObjectStore.prototype.put;
  IDBObjectStore.prototype.put = function(...args) {
    if (studioFault.quota && this.name === 'drafts') throw new DOMException('Synthetic quota','QuotaExceededError');
    return put.apply(this,args);
  };
  const cursorDelete = IDBCursor.prototype.delete;
  IDBCursor.prototype.delete = function(...args) {
    const request = cursorDelete.apply(this,args);
    if (studioFault.deletion) request.addEventListener('success',()=>this.source.transaction.abort());
    return request;
  };
  const remove = IDBObjectStore.prototype.delete;
  IDBObjectStore.prototype.delete = function(...args) {
    const request = remove.apply(this,args);
    if ((studioFault.deletion && this.name === 'drafts') || (studioFault.cleanup && this.name === 'publications')) {
      request.addEventListener('success',()=>this.transaction.abort());
    }
    return request;
  };
})();"""


def close_preview(page):
    try:
        with page.expect_event('close'):
            page.locator('#studio-preview-exit').click(no_wait_after=True)
    except Error:
        # Firefox can close the target before the click protocol reply arrives.
        if not page.is_closed():
            raise
    assert page.is_closed()


def run(browserName, output):
    with tempfile.TemporaryDirectory(prefix='ccs-studio-workflows-') as temporary:
        runtime = Path(temporary)
        (runtime / '.synthetic-publication-test').touch()
        target = runtime / 'target/profiles.json'
        target.parent.mkdir()
        target.write_bytes(encode_document(document()))
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            port = listener.getsockname()[1]
        process, url = launch(runtime, port)
        try:
            with sync_playwright() as pw:
                options = {'headless': True}
                if browserName == 'chromium' and os.environ.get('CS2_CHROMIUM_BIN'):
                    options.update(executable_path=os.environ['CS2_CHROMIUM_BIN'], args=['--no-sandbox'])
                browser = getattr(pw, browserName).launch(**options)
                context = browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='en-US', timezone_id='UTC')
                context.add_init_script(FAULTS)
                faults = []

                def enter(page, resume=False, pending=False):
                    page.on('pageerror', lambda error: faults.append(str(error)))
                    page.goto(url + '/__studio_test__')
                    page.select_option('#locale-select', 'EN')
                    page.locator('#pin').fill(PIN)
                    page.locator('#connect').click()
                    expect(page.locator('#studio-app')).to_be_visible()
                    if resume:
                        page.locator('#studio-dialog button[value="resume"]').click()
                    if not pending:
                        page.wait_for_function('() => CCSStudioTarget.snapshot().state !== null')

                def saved(page):
                    page.wait_for_function("() => ['saved','pristine'].includes(CCSStudioTarget.snapshot().state?.status)")

                def manage(page, action):
                    page.locator('.studio-profile-actions summary').click()
                    page.locator('#studio-' + action).click()

                def confirm(page, value='confirm'):
                    page.locator('#studio-dialog button[value="' + value + '"]').click()

                def title(page, value):
                    page.locator('.w-health').first.click()
                    page.locator('#studio-title').fill(value)
                    page.locator('#studio-title').press('Tab')

                def published(page):
                    page.wait_for_function("() => CCSStudioTarget.snapshot().publication?.code === 'published'")
                    saved(page)

                a = context.new_page()
                enter(a)
                original = target.read_bytes()
                manage(a, 'create')
                a.locator('#studio-dialog-name').fill('Local creation')
                confirm(a)
                a.wait_for_function("() => CCSStudioTarget.snapshot().draft?.baseRevision === 0")
                saved(a)
                createdId = a.evaluate('CCSStudioTarget.snapshot().draft.profileId')
                assert a.evaluate('CCSStudioTarget.snapshot().draft.baseRevision') == 0
                assert target.read_bytes() == original
                a.locator('[data-kind="health"] button').click()
                saved(a)
                assert a.locator('#studio-board .widget').count() == 1
                enter(a, resume=True)
                saved(a)
                assert a.evaluate('CCSStudioTarget.snapshot().draft.profileId') == createdId
                a.locator('#studio-publish').click()
                published(a)
                assert len(json.loads(target.read_bytes())['profiles']) == 3

                # Publishing is followed by a fresh editable baseline, not a closed editor.
                title(a, 'Editable after publication')
                saved(a)
                a.locator('#studio-publish').click()
                published(a)
                assert next(p for p in json.loads(target.read_bytes())['profiles'] if p['id'] == createdId)['revision'] == 2

                # Same profile / same browser detects a competing local write.
                title(a, 'Shared starting draft')
                saved(a)
                b = context.new_page()
                enter(b, resume=True)
                title(a, 'Newer tab A work')
                saved(a)
                title(b, 'Tab B retained in memory')
                b.wait_for_function("() => CCSStudioTarget.snapshot().state?.error === 'local_conflict'")
                assert b.evaluate('CCSStudioTarget.snapshot().draft.configuration.layout.widgets[0].title') == 'Tab B retained in memory'
                b.locator('#studio-recover-copy').click()
                b.locator('#studio-dialog-name').fill('Recovered tab B')
                confirm(b)
                b.wait_for_function("() => CCSStudioTarget.snapshot().draft?.name === 'Recovered tab B'")
                saved(b)
                recoveredId = b.evaluate('CCSStudioTarget.snapshot().draft.profileId')
                assert recoveredId != createdId
                assert a.evaluate('CCSStudioTarget.snapshot().draft.profileId') == createdId
                assert a.evaluate('CCSStudioTarget.snapshot().draft.configuration.layout.widgets[0].title') == 'Newer tab A work'
                b.close()

                # A failed local save never publishes or claims persistence.
                before = target.read_bytes()
                a.evaluate('studioFault.quota=true')
                title(a, 'Unsaved quota work')
                a.wait_for_function("() => CCSStudioTarget.snapshot().state?.error === 'quota_exceeded'")
                expect(a.locator('#studio-alert')).to_contain_text('quota')
                assert target.read_bytes() == before
                a.evaluate('studioFault.quota=false')
                a.locator('#studio-retry').click()
                saved(a)

                # Disk refusal retains the published revision; retry uses the same journal.
                (runtime / 'fail-write.once').touch()
                a.locator('#studio-publish').click()
                a.wait_for_function("() => CCSStudioTarget.snapshot().publication?.code === 'server_error'")
                assert target.read_bytes() == before
                a.locator('#studio-retry').click()
                published(a)

                # Lost acknowledgement is uncertain until the persisted receipt is replayed.
                title(a, 'Lost acknowledgement')
                saved(a)
                (runtime / 'drop-studio-ack.once').touch()
                a.locator('#studio-publish').click()
                a.wait_for_function("() => CCSStudioTarget.snapshot().publication?.code === 'publication_uncertain'", timeout=15000)
                committed = target.read_bytes()
                a.locator('#studio-retry').click()
                published(a)
                assert target.read_bytes() == committed

                # Reload and server restart retain the same uncertain operation identity.
                title(a, 'Restart reconciliation')
                saved(a)
                (runtime / 'drop-studio-ack.once').touch()
                a.locator('#studio-publish').click()
                a.wait_for_function("() => CCSStudioTarget.snapshot().publication?.code === 'publication_uncertain'", timeout=15000)
                committed = target.read_bytes()
                enter(a, pending=True)
                a.wait_for_function("() => CCSStudioTarget.snapshot().publication?.code === 'reconciliation_required'")
                stop(process)
                process, url = launch(runtime, port)
                a.wait_for_function('() => CCSStudioTarget.snapshot().connected')
                a.locator('#studio-retry').click()
                published(a)
                assert target.read_bytes() == committed

                # Later edits survive an acknowledgement received after an explicit keep action.
                title(a, 'Captured before late ack')
                saved(a)
                (runtime / 'hold-studio-ack').touch()
                a.locator('#studio-publish').click()
                a.wait_for_function("() => CCSStudioTarget.snapshot().publication?.code === 'publication_uncertain'",timeout=15000)
                a.locator('#studio-conflict-keep').click()
                title(a, 'Newer edit survives late ack')
                saved(a)
                (runtime / 'hold-studio-ack').unlink()
                a.wait_for_function("() => CCSStudioTarget.snapshot().publication?.code === 'published_draft_retained'")
                assert a.evaluate('CCSStudioTarget.snapshot().draft.configuration.layout.widgets[0].title')=='Newer edit survives late ack'
                assert next(profile for profile in json.loads(target.read_bytes())['profiles'] if profile['id']==createdId)['configuration']['layout']['widgets'][0]['title']=='Captured before late ack'
                a.locator('#studio-conflict-local').click()
                confirm(a)
                published(a)

                # Server commit with failed local cleanup is never reported as server failure.
                title(a, 'Cleanup retained')
                saved(a)
                a.evaluate('studioFault.cleanup=true')
                a.locator('#studio-publish').click()
                a.wait_for_function("() => CCSStudioTarget.snapshot().publication?.code === 'published_cleanup_error'")
                assert a.evaluate('CCSStudioTarget.snapshot().publication.serverCommitted')
                committed = target.read_bytes()
                a.evaluate('studioFault.cleanup=false')
                a.locator('#studio-retry').click()
                published(a)
                assert target.read_bytes() == committed

                # Read-only preview uses the same profile navigation/fullscreen renderer.
                with a.expect_popup() as opened:
                    a.locator('#studio-open-preview').click()
                preview = opened.value
                preview.on('pageerror', lambda error: faults.append(str(error)))
                expect(preview.locator('#board .widget')).to_have_count(1)
                expect(preview.locator('html')).to_have_attribute('data-navigation', 'compact')
                close_preview(preview)
                assert target.read_bytes() == committed

                # Published deletion preserves the local draft for explicit recovery.
                manage(a, 'delete-profile')
                confirm(a, 'delete')
                a.wait_for_function("() => CCSStudioTarget.snapshot().publication?.code === 'published' && CCSStudioTarget.snapshot().readOnly")
                assert all(profile['id'] != createdId for profile in json.loads(target.read_bytes())['profiles'])
                expect(a.locator('#studio-recover-copy')).to_be_visible()
                a.locator('#studio-recover-copy').click()
                a.locator('#studio-dialog-name').fill('Recovered deleted profile')
                confirm(a)
                a.wait_for_function("() => CCSStudioTarget.snapshot().draft?.name === 'Recovered deleted profile'")
                saved(a)
                assert a.evaluate('CCSStudioTarget.snapshot().draft.profileId') != createdId

                revoked = context.new_page()
                enter(revoked, resume=True)
                # Cancelled or failed logout leaves the session and drafts available.
                a.locator('#studio-logout').click()
                confirm(a, 'cancel')
                expect(a.locator('#studio-app')).to_be_visible()
                a.evaluate('studioFault.deletion=true')
                a.locator('#studio-logout').click()
                confirm(a, 'logout')
                expect(a.locator('#studio-alert')).to_contain_text('transaction')
                expect(a.locator('#studio-app')).to_be_visible()
                a.evaluate('studioFault.deletion=false')
                a.locator('#studio-logout').click()
                confirm(a, 'logout')
                expect(a.locator('#studio-login')).to_be_visible()
                # Existing tab handles are revoked; reconnect requires an explicit decision.
                revoked.bring_to_front()
                title(revoked, 'Revoked writer must not persist')
                revoked.wait_for_function('() => CCSStudioTarget.snapshot().blocked')
                expect(revoked.locator('#studio-alert')).to_contain_text('revoked')
                revoked.locator('#studio-retry').click()
                confirm(revoked)
                expect(revoked.locator('#studio-login')).to_be_visible()
                revoked.locator('#pin').fill(PIN)
                revoked.locator('#connect').click()
                revoked.wait_for_function('() => CCSStudioTarget.snapshot().state !== null && !CCSStudioTarget.snapshot().blocked')
                title(revoked, 'Future format stays private')
                saved(revoked)
                profileId = revoked.evaluate('CCSStudioTarget.snapshot().draft.profileId')
                revoked.evaluate('''async id=>{
                  const db=await new Promise((resolve,reject)=>{const r=indexedDB.open('ccs-local-drafts',2);r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});
                  try { await new Promise((resolve,reject)=>{const tx=db.transaction('drafts','readwrite');const store=tx.objectStore('drafts');const req=store.openCursor();
                    req.onsuccess=()=>{const cursor=req.result;if(!cursor)return;const value=cursor.value;if(value.draft.profileId===id){value.draft.version=99;cursor.update(value);}cursor.continue();};
                    tx.oncomplete=resolve;tx.onabort=()=>reject(tx.error);}); } finally {db.close();}
                }''',profileId)
                enter(revoked,pending=True)
                expect(revoked.locator('#studio-alert')).to_contain_text('not supported')
                expect(revoked.locator('#studio-recover-copy')).to_be_hidden()
                assert revoked.evaluate('CCSStudioTarget.snapshot().draft') is None
                revoked.locator('#studio-discard-draft').click()
                confirm(revoked,'discard')
                revoked.wait_for_function("()=>CCSStudioTarget.snapshot().state?.status==='pristine'")
                assert not faults, faults
                if output:
                    output.mkdir(parents=True, exist_ok=True)
                    (output / 'workflows.json').write_text(json.dumps({'browser': browser.version,
                        'creationResume': True, 'editableAfterPublication': True, 'tabConflictRecovery': True,
                        'quotaRetry': True, 'diskRetry': True, 'lostAckReplay': True, 'cleanupRetry': True,
                        'preview': True, 'deletionRecovery': True, 'logoutFailure': True, 'errors': faults}, indent=2), encoding='utf8')
                browser.close()
                beforeReopen = target.read_bytes()
                with tempfile.TemporaryDirectory(prefix='ccs-studio-persistent-browser-') as userData:
                    retainedId = None
                    for reopening in [False, True]:
                        persistent = getattr(pw,browserName).launch_persistent_context(userData,
                            **options,viewport={'width':1920,'height':1080},locale='en-US',timezone_id='UTC')
                        persistentPage = persistent.new_page()
                        enter(persistentPage,resume=reopening)
                        if not reopening:
                            manage(persistentPage,'create')
                            persistentPage.locator('#studio-dialog-name').fill('Survives browser process closure')
                            confirm(persistentPage)
                            persistentPage.wait_for_function("()=>CCSStudioTarget.snapshot().draft?.baseRevision===0")
                            saved(persistentPage)
                            retainedId=persistentPage.evaluate('CCSStudioTarget.snapshot().draft.profileId')
                        else:
                            assert persistentPage.evaluate('CCSStudioTarget.snapshot().draft.profileId')==retainedId
                            assert persistentPage.evaluate('CCSStudioTarget.snapshot().draft.name')=='Survives browser process closure'
                        persistent.close()
                assert target.read_bytes()==beforeReopen
                assert not faults,faults
                print('OK: Studio creation/resume, repeated editing, tab recovery, quota/disk/ack/cleanup faults, preview, deletion recovery and logout')
        finally:
            stop(process)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser', choices=['chromium', 'firefox', 'webkit'], default='chromium')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    run(args.browser, args.output)
