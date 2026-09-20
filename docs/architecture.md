# SurfIntel — architectuur

SurfIntel is een open cyber threat intelligence platform voor SURF en
aangesloten onderwijs- en onderzoeksinstellingen. Het aggregeert
security-nieuws, vendor-advisories en CERT-bulletins, verrijkt deze
automatisch (CVE/CPE/KEV/categorisatie), en laat instellingen daarop
alerts abonneren.

## Stack

- **Backend**: Python, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL.
- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS.
- **Notificaties**: [Apprise](https://github.com/caronc/apprise) (mail, Slack, Teams, webhook, ...).
- **Deployment**: Docker Compose (lokaal en later self-hosted).
- **Licentie**: GPLv3.

## Ingestion-pipeline

Een **source** (RSS-feed of custom module) levert periodiek een lijst
van *links* — een RSS-feed bevat vaak niet de volledige informatie, dus
het item op de link zelf is de eenheid die gevolgd wordt, niet de
feed-entry.

Elke link wordt een **item**: gededupliceerd op URL, opgehaald via een
pluggable fetch-backend (nu: directe HTTP-fetch; later eventueel een
zelf gehoste [changedetection.io](https://changedetection.io)-instance
via zijn REST API voor vendor-advisorypagina's zonder RSS die
JS-rendering of doorlopende wijzigingsdetectie nodig hebben — altijd
puur als ingestion-bron, nooit als system-of-record).

Na het ophalen draait een **enrichment-pipeline**: een reeks losse,
onafhankelijke modules (CVE-extractie, CPE-extractie, CISA
KEV-check, AI-categorisatie) die elk hun eigen resultaat wegschrijven
in `item_enrichment`, gekoppeld aan het item. Nieuwe modules kunnen
later worden toegevoegd zonder de rest van de pipeline te wijzigen.

**MVP-keuze:** dit draait synchroon, in vaste volgorde, direct na het
ophalen — geen job-queue. Er wordt alleen de laatste inhoud +
een `content_hash`/`last_changed_at` bijgehouden, geen volledige
revisiehistorie. Beide keuzes zijn bewust gemaakt om infra simpel te
houden; de module-interfaces zijn zo ontworpen dat een latere
overstap naar een job-queue een kwestie van vervangen is, geen
herontwerp.

## Multi-tenancy & rollen

Eén gedeelde item-feed voor alle instellingen; wat per instelling
verschilt zijn de saved queries (alert-regels) en instellingen. Elke
gebruiker hoort bij precies **één** organisatie (`app_user.organization_id`),
met een rol `admin` of `viewer` binnen die organisatie. Een
platformbrede super-admin is geen los concept: SURF zelf is een
`organization`-rij (`is_platform_operator = true`) en platform-admins
zijn gebruikers van die organisatie met `is_platform_admin = true`.

**Tenant-isolatie** gebeurt op applicatieniveau: één centrale
query-helper (`api/deps.py`) injecteert altijd `organization_id` uit
de JWT-sessie. Platform-admin routes zijn de enige, expliciete
uitzondering. Dit is een bewuste MVP-keuze (versus Postgres
row-level-security) om infra/opzetwerk te beperken.

**Auth** is pluggable via een `AuthProvider`-interface: nu
`local_password`, later `saml_surfconext` voor SURFconext SSO — beide
resolven naar een `app_user`-rij en geven dezelfde JWT terug.

## Alerting

Een alert-regel (`alert_rule`) bestaat uit een of meer
`alert_condition`-rijen (veld + lijst van waarden) die **allemaal**
moeten kloppen (AND), waarbij meerdere waarden binnen één veld een OR
zijn — bv. `vendor IN [Ivanti, Fortinet] AND severity IN [kritiek, hoog]`.
Dit dekt de praktijk zonder een volledige boolean-expressie-parser
nodig te hebben.

Na de enrichment-pipeline bouwt de **match-view** één plat object per
item: elke enrichment-module declareert zelf welke velden hij
bijdraagt (CVE-extractie levert `cve_id`, KEV-check levert
bv. `in_kev`, categorisatie levert `severity`/`category`), plus een
`keyword`-veld (titel + tekst, voor substring-matches). Nieuwe
enrichment-modules worden zo automatisch bruikbaar als alert-veld.

Bij een match wordt een `alert_match`-rij aangemaakt (unique op
`alert_rule_id, item_id` — idempotent, nooit dubbel notificeren) en
wordt de notificatie verstuurd via de Apprise-URL's in
`alert_channel`. **Apprise-URL's staan versleuteld in de database**
(ze bevatten vaak tokens/wachtwoorden) en worden na aanmaken nooit
meer volledig teruggegeven, alleen gemaskeerd.

Ook dit draait, consistent met de enrichment-pipeline, synchroon
in-process; dezelfde overweging (nu simpel, later evt. een queue)
geldt hier.

## Databaseschema (kern)

```
organization(id, name, slug, sso_entity_id, is_platform_operator, is_active, created_at)

app_user(id, organization_id, email, name, role[admin|viewer],
         is_platform_admin, password_hash, is_active, created_at, last_login_at)

source(id, name, type[rss|custom_module], config, enabled,
       poll_interval_seconds, last_polled_at, created_at)

item(id, source_id, url, title, published_at, status,
     content_hash, last_changed_at, raw_html, extracted_text,
     first_seen_at, last_checked_at)

item_enrichment(id, item_id, module_name, module_version, data,
                created_at)  -- unique(item_id, module_name)

alert_rule(id, organization_id, created_by, name,
           status[active|paused], created_at, updated_at)

alert_condition(id, alert_rule_id,
                 field[vendor|product|severity|category|cve_id|source|tag|keyword],
                 values)

alert_channel(id, alert_rule_id, label, apprise_url_encrypted,
              enabled, created_at)

alert_match(id, alert_rule_id, item_id, matched_at, notified_at,
            notification_status[pending|sent|failed])  -- unique(alert_rule_id, item_id)
```

## Design

Visuele richting geïnspireerd op de SURF-huisstijl: licht, kleurrijk,
met blauw (#003da5 / #0077c8) als primaire kleur en teal/groen/paars/
rood als categorie-accenten. Typografie: Space Grotesk (koppen) +
IBM Plex Sans (body) + IBM Plex Mono (CVE-ID's/code).

## Bewust uitgesteld (nog niet gebouwd)

- CVE/actor/campagne-correlatiegraaf (nice-to-have, latere fase).
- Volledige revisiehistorie per item.
- Async job-queue voor enrichment/alerting.
- Postgres row-level-security als extra verdedigingslaag.
- SURFconext SAML2-implementatie (interface staat klaar, provider nog niet gebouwd).
