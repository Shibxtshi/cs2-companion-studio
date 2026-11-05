# Licensing and redistribution

The English [Community No-Resale License v1.0](../../LICENSE) is the authoritative text. The [French translation](LICENSE.fr.md) is informative. This guide summarizes the terms; it does not replace them or create additional permissions.

## Integration and publication status

This license integration takes effect only after the maintainer expressly authorizes and merges the dedicated license PR, subject to the final text and the rights the licensor can grant. A proposed branch or open PR is not adoption. Neither that merge nor the code version announces a public software release, tag, visibility change or deployment. The maintainer has chosen to proceed without commissioning a lawyer; the text has not been certified or approved by a qualified legal professional.

Section 13 preserves permissions validly obtained under earlier licenses, mandatory rights and third-party licenses. Replacing LICENSE does not retroactively grant new rights or revoke valid earlier ones. Shibxtshi is the identified maintainer pseudonym, established in France, not a certification of exclusive ownership of every repository element.

## What the terms distinguish

CCS is proprietary, **source-available, not OSI-approved open source**. Source visibility is not the same as unrestricted resale; see the [OSI definition](https://opensource.org/osd).

| Activity | Summary and authoritative sections |
|---|---|
| Personal, internal and professional use | Permitted, including monetized streaming and coaching. Internal modifications need not be published. Internal scope includes the entity, group companies and controlled authorized providers; external customers are not internal merely by contract (§§1–3). |
| Free redistribution and modifications | Permitted subject to notices, attribution, change identification and the applicable source/no-resale terms. Each executable recipient receives complete corresponding source, modifications and reconstruction instructions immediately and free with delivery; an additional link is optional, not a substitute (§4). |
| Software resale and paid functionality | Paid copies, paid Pro editions, serial resale and subscriptions selling access to CCS functions are prohibited for original and modified CCS (§5). |
| Donations | Voluntary donations and symbolic acknowledgments are permitted; no paid early access, donor-only version or exclusive function (§5). |
| Paid custom development | Genuine commissioned work and delivery to a client are permitted with source and attribution, not standardized Pro resale disguised as a commission (§6). |
| Hardware and independent services | May be sold with CCS supplied free, also obtainable separately without mandatory purchase. Optional paid installation, configuration, support and maintenance must not sell a software entitlement (§6). |
| Managed private instances | Genuine infrastructure/operations may be paid; customers retain the materials and ability to run CCS independently. A functional paywall cannot be relabeled hosting. Modified hosted versions provide external users free corresponding-source access throughout operation (§§7–8). |
| Identity and forks | Unchanged copies may retain official identity. Public modified forks use a distinct name and logo, may identify CCS origin and retain notices without claiming endorsement (§10). |
| Independent creations | Mere compatibility does not subject independent works to CCS terms; copied/adapted protectable CCS portions remain distinct (§2). |

Keep PINs, tokens, personal profiles, credentials and game/private data out of source deliveries. Privacy is not a reason to withhold covered code by merely labeling it confidential (§4). Hosting permissions are legal terms, **not technical approval for Internet exposure**: follow [SECURITY.md](../../SECURITY.md); CCS is not a public multi-user hosting platform.

## Contributions and third-party material

Contributors retain their rights. Section 9 requires explicit authorization from the entitled person for incorporation, reproduction, modification and redistribution under the identified supplied license, including downstream permissions. A submission or Git author entry alone is insufficient. No general authority to relicense future contributions under different terms is presumed. Follow [CONTRIBUTING.md](../../CONTRIBUTING.md).

Inter and Barlow Condensed remain under SIL OFL 1.1, with their [notices and provenance](../../static/fonts/README.md). Dependencies keep their own licenses. The CCS no-resale condition does not relicense separately licensed components. See the [official OFL text](https://openfontlicense.org/open-font-license-official-text/). Preserve the notices applying to material actually redistributed.

## Official V1.0.0 artifact

The selected official distribution is **one source ZIP**, including the Windows installer, Dockerfile and Compose configuration. **No prebuilt Docker image is published.** Local builds/downloaded dependencies do not make their installed packages part of that source ZIP. Any future image distribution needs a separate inventory of the components actually included.

Before a separately authorized release, check the exact final ZIP for the authoritative LICENSE, informative translation, font notices/provenance and absence of private context, reports, profiles and secrets. See the [release checklist](../releases/checklist.md). A prior draft ZIP is not the approved final artifact.
