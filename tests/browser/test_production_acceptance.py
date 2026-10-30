"""P10 acceptance journeys against the production ASGI composition only."""
import argparse
import json
import os
from pathlib import Path
import tempfile

from playwright.sync_api import expect, sync_playwright
from test_production_studio import production, login, PIN

RESOLUTIONS = [(1920,1080), (1366,768), (1280,900), (1024,768), (768,1024), (390,844), (320,740)]


def saved(page):
    expect(page.locator('#studio-save-state')).to_contain_text('Draft kept locally')


def publish(page):
    page.locator('#studio-publish').click()
    expect(page.locator('#studio-save-state')).to_contain_text('Published version up to date')


def field(page, name, value):
    page.locator('#' + name).fill(str(value))
    page.locator('#' + name).press('Tab')


def management(page, action):
    page.locator('.studio-profile-actions summary').click()
    page.locator('#studio-' + action).click()


def name_profile(page, value):
    page.locator('#studio-dialog-name').fill(value)
    page.locator('#studio-dialog button[value="confirm"]').click()
    expect(page.locator('#studio-profile option:checked')).to_contain_text(value)


def workflow(browser, output):
    with production() as (url, data, _initial, _restart):
        # Keep mouse pointer input distinct from the touch-context coverage in test_studio_matrix.
        context = browser.new_context(viewport={'width':1920,'height':1080})
        page = context.new_page()
        faults = []
        page.on('pageerror', lambda error: faults.append(str(error)))
        login(page, url)
        page.locator('[data-section="studio"]').click()
        for language, obsolete in [('FR','isolé de ton installation'),('EN','isolated from your current installation')]:
            page.select_option('#locale-select',language)
            page.locator('#studio-help').click()
            expect(page.locator('#studio-dialog-message')).not_to_contain_text(obsolete)
            page.locator('#studio-dialog button[value="cancel"]').click()
        management(page, 'create')
        name_profile(page, 'P10 local creation')
        saved(page)
        selectedId = page.locator('#studio-profile').input_value()
        assert selectedId not in [profile['id'] for profile in json.loads((data / 'profiles.json').read_bytes())['profiles']]
        page.locator('.studio-library-item[data-kind="health"] button').click()
        expect(page.locator('#studio-board>.widget')).to_have_count(1)
        page.select_option('#studio-variant', 'compact')
        field(page, 'studio-title', 'P10 personal title')
        field(page, 'studio-x', 2)
        field(page, 'studio-y', 3)
        field(page, 'studio-width', 8)
        field(page, 'studio-height', 6)
        saved(page)
        page.locator('#studio-duplicate').click()
        expect(page.locator('#studio-board>.widget')).to_have_count(2)
        page.locator('#studio-remove').click()
        page.locator('#studio-dialog button[value="remove"]').click()
        expect(page.locator('#studio-board>.widget')).to_have_count(1)
        page.locator('#studio-board>.widget').click(position={'x':15,'y':15})
        beforeY = int(page.locator('#studio-y').input_value())
        handle = page.locator('[data-studio-gesture="move"]')
        handle.scroll_into_view_if_needed()
        box = handle.bounding_box()
        page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
        page.mouse.down()
        page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2 + 40, steps=4)
        page.mouse.up()
        expect(page.locator('#studio-y')).to_have_value(str(beforeY + 1))
        page.locator('#studio-undo').click()
        expect(page.locator('#studio-y')).to_have_value(str(beforeY))
        page.locator('#studio-redo').click()
        expect(page.locator('#studio-y')).to_have_value(str(beforeY + 1))
        saved(page)
        beforeHeight = int(page.locator('#studio-height').input_value())
        resize = page.locator('[data-studio-gesture="resize"]')
        resize.scroll_into_view_if_needed()
        box = resize.bounding_box()
        page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
        page.mouse.down()
        expect(page.locator('.studio-placement-ghost')).to_be_visible()
        page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2 + 40, steps=4)
        page.mouse.up()
        expect(page.locator('#studio-height')).to_have_value(str(beforeHeight + 1))
        page.locator('#studio-undo').click()
        expect(page.locator('#studio-height')).to_have_value(str(beforeHeight))
        page.locator('#studio-redo').click()
        expect(page.locator('#studio-height')).to_have_value(str(beforeHeight + 1))
        saved(page)
        geometry = [page.locator('#studio-' + key).input_value() for key in ['x','y','width','height']]
        for width, height in RESOLUTIONS:
            page.set_viewport_size({'width':width,'height':height})
            page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
            if not page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'):
                output.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(output / ('overflow-' + str(width) + '.png')), full_page=True)
                excess = page.evaluate('() => ({window:innerWidth,root:document.documentElement.scrollWidth,body:document.body.scrollWidth,x:scrollX,nodes:[...document.querySelectorAll("body *")].filter(node=>node.getBoundingClientRect().right+scrollX>innerWidth+1||node.scrollWidth>node.clientWidth+1).slice(0,20).map(node=>({id:node.id,tag:node.tagName,classes:node.className,right:node.getBoundingClientRect().right,scroll:node.scrollWidth,width:node.clientWidth}))})')
                raise AssertionError((width,height,excess))
        page.set_viewport_size({'width':1920,'height':1080})
        assert [page.locator('#studio-' + key).input_value() for key in ['x','y','width','height']] == geometry
        publish(page)
        document = json.loads((data / 'profiles.json').read_bytes())
        current = next(profile for profile in document['profiles'] if profile['id'] == selectedId)
        assert current['configuration']['layout']['widgets'][0]['variant'] == 'compact'
        assert page.locator('#dashboard-profile-menu').input_value() == selectedId

        beforeCopy=(data/'profiles.json').read_bytes()
        management(page,'copy-profile')
        name_profile(page,'P10 duplicated profile')
        saved(page)
        assert (data/'profiles.json').read_bytes()==beforeCopy
        copiedId=page.locator('#studio-profile').input_value()
        assert copiedId!=selectedId
        publish(page)
        copied=next(profile for profile in json.loads((data/'profiles.json').read_bytes())['profiles'] if profile['id']==copiedId)
        assert copied['configuration']==current['configuration']
        management(page,'delete-profile')
        page.locator('#studio-dialog button[value="delete"]').click()
        expect(page.locator('#studio-save-state')).to_contain_text('deleted')
        afterDelete=json.loads((data/'profiles.json').read_bytes())
        assert all(profile['id']!=copiedId for profile in afterDelete['profiles'])
        assert any(item['id']==copiedId for item in afterDelete['tombstones'])
        page.select_option('#studio-profile',selectedId)
        expect(page.locator('#studio-board>.widget')).to_have_count(1)

        page.locator('#studio-board>.widget').click(position={'x':15,'y':15})
        field(page, 'studio-title', 'P10 unpublished')
        saved(page)
        original = (data / 'profiles.json').read_bytes()
        page.locator('.studio-brand').click()
        page.locator('#studio-dialog button[value="cancel"]').click()
        expect(page.locator('#studio-app')).to_be_visible()
        assert (data / 'profiles.json').read_bytes() == original
        page.locator('.studio-brand').click()
        page.locator('#studio-dialog button[value="keep"]').click()
        expect(page.locator('#studio-app')).to_be_hidden()
        page.locator('[data-section="studio"]').click()
        page.locator('#studio-dialog button[value="resume"]').click()
        expect(page.locator('#studio-board>.widget')).to_contain_text('P10 unpublished')
        page.locator('.studio-brand').click()
        page.locator('#studio-dialog button[value="discard"]').click()
        page.locator('#studio-dialog button[value="discard"]').click()
        expect(page.locator('#studio-app')).to_be_hidden()
        assert (data / 'profiles.json').read_bytes() == original
        page.locator('[data-section="studio"]').click()
        page.locator('#studio-board>.widget').click(position={'x':15,'y':15})
        field(page, 'studio-title', 'P10 explicit exit publication')
        saved(page)
        page.locator('.studio-brand').click()
        page.locator('#studio-dialog button[value="publish"]').click()
        expect(page.locator('#studio-app')).to_be_hidden()
        expect(page.locator('#board>.widget')).to_contain_text('P10 explicit exit publication')
        page.locator('[data-section="studio"]').click()
        with page.expect_popup() as opening:
            page.locator('#studio-open-preview').click()
        preview = opening.value
        expect(preview.locator('#board>.widget')).to_have_count(1)
        assert preview.url == url + '/preview'
        preview.close()
        page.locator('#studio-profile-tab').click()
        field(page, 'studio-profile-name', 'P10 renamed')
        page.select_option('#studio-theme', 'creator-purple')
        page.select_option('#studio-navigation', 'hidden')
        page.locator('#studio-floating').uncheck()
        saved(page)
        publish(page)
        page.locator('.studio-brand').click()
        expect(page.locator('html')).to_have_attribute('data-navigation','hidden')
        expect(page.locator('.navigation-float')).to_be_hidden()
        page.locator('.navigation-edge').click()
        page.locator('[data-section="settings"]').click()
        expect(page.locator('#production-profile-preferences')).to_contain_text('P10 renamed')
        page.locator('.topbar [data-dashboard-home]').focus()
        page.keyboard.press('Enter')
        expect(page.locator('html')).to_have_attribute('data-section','dashboard')
        page.keyboard.press('Alt+m')
        page.locator('[data-section="settings"]').click()
        page.locator('#settings-help').click()
        expect(page.locator('#help-dialog')).to_be_visible()
        page.keyboard.press('Escape')
        page.locator('.topbar [data-dashboard-home]').click()
        page.locator('#dashboard-fullscreen').click()
        expect(page.locator('html')).to_have_attribute('data-immersive','true')
        page.keyboard.press('Escape')
        expect(page.locator('html')).to_have_attribute('data-immersive','false')
        assert page.locator('#dashboard-profile-menu').input_value() == selectedId
        output.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(output / 'published-dashboard.png'))
        assert not faults, faults
        context.close()
    print('PASS: native production profile creation, geometry, gesture/history, seven resolutions, four exit choices, preview and hidden-navigation recovery', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', choices=['chromium','firefox','webkit'], default='chromium')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with sync_playwright() as playwright:
        options = {}
        if args.browser == 'chromium' and os.environ.get('CCS_CHROMIUM_EXECUTABLE'):
            options['executable_path'] = os.environ['CCS_CHROMIUM_EXECUTABLE']
        browser = getattr(playwright,args.browser).launch(headless=True, **options)
        try:
            workflow(browser,args.output)
        finally:
            browser.close()
