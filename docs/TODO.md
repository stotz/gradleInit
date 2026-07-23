# TODO

[README.md](../README.md)  

[SECURITY.md](SECURITY.md)  
[REPOSITORIES.md](REPOSITORIES.md)

---

[![TODO](https://img.shields.io/badge/TODO-blue.svg)](TODO)




## Aktueller Stand (v0063)

gradleInit ist ein Python-basiertes Tool zur Generierung von Kotlin/Gradle-Projekten aus Templates.
Verwendet Jinja2 fuer Template-Verarbeitung mit inline Hint-System.
SCRIPT_VERSION (semantisch, Git-Repo) ist aktuell 1.12.7; die 4-stellige AI-Versionierung
ist davon getrennt und laeuft linear (zuletzt v0063).

Hinweis zur History: Die Versionstabelle unten ist zwischen v0023 und v0024 unvollstaendig.
Einige Features (erweiterte Hint-Syntax mit Regex, Template-Compilation-Cache) sind im Code
vorhanden, wurden aber in vorhergehenden Chats nicht einzeln in der History dokumentiert.
Sie sind hier nicht rekonstruiert, um keine erfundenen Versionseintraege zu erzeugen.

Hauptfeatures:
- Template-basierte Projektgenerierung (init Command)
- Subproject-Generierung fuer Multi-Module-Projekte (subproject Command)
- Unterstuetzung fuer lokale und Remote-Templates (GitHub)
- Inline Hint-Syntax fuer selbstdokumentierende Templates
- Gradle Wrapper Generierung und Git-Initialisierung
- Optionale Module (Maven Central, Spring Boot BOM)
- Repository-Signierung und Verifikation (RSA-4096, SHA-256)
- npm-style Version Constraints (@pin, @*, @^, @~)
- Version Updates via `gradleInit versions --check/--update`
- JDK 24 Cap fuer Kotlin jvmToolchain (Kotlin 2.x Maximum)
- --latest Flag fuer @* statt @pin Version-Constraints

## Aktuelle Arbeit

v0063: --audit-sources --fix (SWITCH-Befunde automatisch anwenden)

- Der dias-Audit zeigte den SWITCH fuer beryx_jlink korrekt an, verlangte aber manuelles
  Editieren der URL. Neu: 'gradleInit versions --audit-sources --fix' schreibt die
  vorgeschlagene authoritative URL direkt in die Kommentarzeile des Katalogs
  (VersionManager.update_source_url: ersetzt nur die URL, Policy-Token und Version
  bleiben unangetastet, LF via write_text_lf). Danach hebt 'versions --update' die
  Version aus der neuen Quelle (z.B. beryx 3.1.5 -> 4.1.0). Ohne --fix weist der Audit
  auf das Flag hin. Analog 'version_sync --audit --fix' fuer die SSoT.
- Exit-Verhalten: nach erfolgreichem --fix zaehlen die behobenen SWITCHes nicht mehr als
  Findings (Exit 0, sofern keine STALE/fehlgeschlagenen Fixes bleiben) - CI-tauglich.
- Verifiziert am nachgestellten dias-Katalog: URL getauscht, @*-Token und Version
  erhalten, Re-Audit komplett gruen, LF erhalten.
- Tests: TestAuditSources erweitert (Fix schreibt URL, Version unberuehrt, Re-Audit OK).
  Suite 150 passed.
- Betroffenes Repo: gradleInit (gradleInit.py, tools/version_sync.py,
  test_gradleInit.py).

v0062: Selfupdate-Pull mit Terminal (SSH-Passphrase-Prompt) + Live-Bestaetigung Audit

- Befund aus '--update all' auf bootes: der gradleInit-Selfupdate rief
  'git pull --ff-only' mit capture_output auf. Ohne Terminal kann ssh keine
  Key-Passphrase abfragen -> aus einem passphrase-geschuetzten Key wird
  "Permission denied (publickey)". (Templates/Modules liefen, weil sie ueber HTTPS
  anonym gelesen werden.) Mit geladenem ssh-agent lief der Pull dann durch - der
  Fix haertet den Fall OHNE Agent.
- Fix: der Pull laeuft jetzt mit geerbtem stdio (Prompts moeglich, git-Ausgabe direkt
  sichtbar); im Fehlerfall nennt die Meldung die typischen Ursachen inkl. konkreter
  Kommandos (ssh-agent/ssh-add bzw. remote set-url auf HTTPS).
- Live-Bestaetigung der v0057-v0061-Kette auf bootes: nach 'gradleInit modules
  --update' zeigt der dias-Audit korrekt [SWITCH] beryx_jlink -> Portal 4.1.0
  (12 ok, 1 switch, 0 unknown) - der Detektor arbeitet gegen die echten Registries.
- Tests: TestSelfUpdateGitInteractive (Pull ohne capture_output; Fehlerpfad nennt
  ssh-add-Hinweis). Suite 149 passed.
- Betroffenes Repo: gradleInit (gradleInit.py, test_gradleInit.py).

v0061: Audit unterscheidet "Resolver fehlt" von "Artefakt existiert nicht"

- Befund aus dem ersten Real-Lauf auf bootes (dias-Projekt): beryx_jlink erschien als
  "[??] not found on either registry", obwohl das Plugin auf dem Portal liegt. Ursache
  auf der Maschine: das Portal-Resolver-Modul (v1.12.7) war lokal nicht installiert
  (erkennbar auch daran, dass die NOT_FOUND-Meldung von versions --update keinen
  Portal-Hint trug). Der Audit behauptete jedoch, beide Registries geprueft zu haben.
- Fix: audit_version_sources unterscheidet jetzt Resolver-Verfuegbarkeit von echter
  Abwesenheit. Meldungen nennen die Ursache ("Gradle Plugin Portal resolver not
  installed - run: gradleInit modules --update"). Sicherheitsregel: fehlt der Resolver
  der KONFIGURIERTEN Quelle, wird nie ein SWITCH auf die andere Registry empfohlen
  (die koennte ein stale Spiegel sein) - stattdessen UNKNOWN mit "authority unverified".
  Schlusszeile sagt bei verbleibenden UNKNOWNs nicht mehr "all sources authoritative".
- Verifiziert: bootes-Fall nachgestellt (ohne Portal-Resolver: klare UNKNOWN-Meldungen;
  mit Resolver: beryx SWITCH mit Portal-URL, cyclonedx OK mit "mirror behind").
- Tests: TestAuditSources um Verfuegbarkeits-Faelle erweitert (kein falsches
  "not found on either", kein SWITCH auf unverifizierte Quelle). Suite 147 passed.
- Hinweise fuer die Maschinen: 'gradleInit modules --update' installiert den
  Portal-Resolver; danach zeigt der dias-Audit fuer beryx_jlink den SWITCH mit
  https://plugins.gradle.org/plugin/org.beryx.jlink (Katalog dort auf Portal-URL +
  4.1.0 stellen). Nebenbefund aus dem Lauf: SSoT hinkt inzwischen (shadow 9.6.1,
  javafx 26.0.2) -> naechster update_all_versions.sh-Lauf zieht Templates nach.
- Betroffenes Repo: gradleInit (gradleInit.py, test_gradleInit.py).

v0060: versions --audit-sources und version_sync --audit (Beide-Quellen-Vergleich)

- Schliesst die Restluecke aus v0059: der Stale-Detektor griff nur, wenn die lokale
  Version bereits neuer war als der Spiegel. Der Audit vergleicht jetzt JEDEN
  URL-gestuetzten Eintrag mit BEIDEN Registries (Maven Central + Gradle Plugin Portal),
  unabhaengig vom lokalen Stand.
- Verdikte: OK (konfigurierte Quelle authoritativ; nennt informativ, wenn die andere
  Registry ein veralteter Spiegel ist), SWITCH (andere Registry neuer oder Artefakt auf
  der konfigurierten fehlt -> konkrete Umstell-URL wird ausgegeben), STALE (Quelle
  aelter als lokale Version), UNKNOWN (nirgends gefunden). Exit 1 bei SWITCH/STALE
  (CI-tauglich). Templated-Eintraege (kotlin/jdk) werden uebersprungen.
- Kernfall abgedeckt: Eintrag selbst veraltet (z.B. cdx 2.0.0) + Central-Spiegel 1.4.0
  -> v0059 haette geschwiegen, der Quervergleich meldet SWITCH auf Portal 3.3.0.
- Zwei Einstiege: 'gradleInit versions --audit-sources' (Projekt-/Template-Kataloge,
  braucht settings.gradle.kts) und 'python tools/version_sync.py --audit' (SSoT).
  Implementierung als gemeinsame Modul-Funktionen audit_version_sources +
  print_source_audit in gradleInit.py.
- Tests: TestAuditSources (alle Verdikte inkl. Kernfall, Findings-Zaehlung, Skip der
  Platzhalter). Suite 145 passed.
- OFFEN: Live-Lauf gegen beide Registries auf Deiner Maschine
  (python tools/version_sync.py --audit) - erwartet: alles OK/gruen.
- Betroffenes Repo: gradleInit (gradleInit.py, tools/version_sync.py,
  test_gradleInit.py).

v0059: Stale-Mirror-Detektor (Antwort auf "wie entdecken wir solche Faelle?")

- Kernsignal: meldet eine Quelle als "latest" eine Version, die AELTER ist als unsere
  aktuelle, kann die Quelle nicht die gepflegte Registry sein (cyclonedx: Central 1.4.0
  vs. unsere 3.3.0). check_updates flaggt das jetzt als [STALE!] STALE_SOURCE mit
  Klartext-Meldung, statt still "up to date"/Downgrade-Logik laufen zu lassen.
- Zweites Signal fuer Gradle-Plugin-Marker (artifactId endet auf .gradle.plugin): bei
  STALE_SOURCE und bei NOT_FOUND wird automatisch das Plugin Portal gegengeprueft; hat
  es eine >= aktuelle Version, nennt die Meldung die konkrete Umstell-URL
  (https://plugins.gradle.org/plugin/<id>). Beide historischen Faelle (cyclonedx stale,
  beryx_jlink not-found) haetten damit sofort die richtige Anweisung geliefert.
- Ausgabe: 'versions' zeigt [STALE!]-Zeilen und einen Summary-Hinweis
  ("N STALE SOURCE(S) - action needed"); version_sync --update ebenso.
- Tests: TestStaleSourceDetection (stale lib, stale Marker mit Portal-Hint, not-found
  Marker mit Portal-Hint, normales Update bleibt UPDATE).
- Betroffenes Repo: gradleInit (gradleInit.py, tools/version_sync.py,
  test_gradleInit.py).

v0058: beryx_jlink auf Plugin Portal umgestellt und auf 4.1.0 angehoben

- Gleicher Fall wie cyclonedx (v0057): die mvnrepository-URL fuer
  org.beryx.jlink.gradle.plugin fuehrte ins Leere (bisher dauerhaft
  "[SKIP] not on Maven Central"), waehrend die aktuelle 4.1.0 auf dem Gradle Plugin
  Portal liegt. Das kotlin-javaFX-Template stand dadurch veraltet auf 3.1.5.
- Fix ueber die SSoT-Maschine: SSoT-URL auf
  https://plugins.gradle.org/plugin/org.beryx.jlink @* gestellt und Version auf 4.1.0
  (vom DiaS-UI-Projekt real gebaut); Template-Katalog-Kommentar ebenso auf die
  Portal-URL. version_sync --apply hat Template-Katalog und den kotlin-javaFX-README-
  Span konvergiert; --check gruen.
- Verifiziert: der Portal-Resolver (v0057) uebersetzt die neue URL in die
  Marker-Koordinaten (org.beryx.jlink / org.beryx.jlink.gradle.plugin) und loest den
  Eintrag auf (statt NOT_FOUND); version_sync- und Portal-Tests gruen (24), alles LF.
  Damit wird beryx_jlink kuenftig automatisch mitgepflegt.
- OFFEN: kotlin-javaFX-Build mit jlink 4.1.0 (kein Gradle im Sandbox; DiaS UI mit 4.1.0
  ist ein starkes Signal, das Template selbst aber ungebaut - zusammen mit
  validatorfx 1.0.0 beim naechsten ./gradlew build pruefen).
- Betroffene Repos: gradleInit (SSoT), gradleInitTemplates (kotlin-javaFX
  Katalog-URL + Version, README-Span).

v0057: Gradle-Plugin-Portal-Resolver (cyclonedx-URL-Korrektur)

- Korrektur zu v0056: Maven Central traegt vom CycloneDX-Plugin nur den veralteten Spiegel
  (org.cyclonedx/cyclonedx-gradle-plugin: 1.4.0 von 2021); die aktuelle 3.3.0 liegt nur
  auf dem Gradle Plugin Portal. mvnrepository-URL waere als Update-Quelle falsch gewesen.
- Statt Dauer-SKIP: neuer Resolver GradlePluginPortal in gradleInitModules
  (resolvers/gradle_plugin_portal.py) - Subklasse von MavenCentral, denn das Portal ist
  ein Standard-Maven-Repo unter https://plugins.gradle.org/m2 (maven-metadata.xml,
  Plugin-Marker <id>:<id>.gradle.plugin). Eigener Cache (cache/plugin-portal), kein
  Search-API-Fallback (Portal hat keine). In MODULES.toml registriert.
- gradleInit.py: URL_PATTERN akzeptiert plugins.gradle.org/plugin/<id>-URLs;
  extract_artifact_coords liefert die Marker-Koordinaten; check_updates waehlt den
  Resolver pro Eintrag (Portal-URL -> Portal, sonst Maven Central), Meldungen nennen die
  Quelle; fehlt der Portal-Resolver, gibt es einen klaren SKIP-Hinweis (modules --update).
  handle_versions_command und version_sync run_update laden den Portal-Resolver mit.
- cyclonedx-URLs in SSoT und allen 5 Template-Katalogen auf
  https://plugins.gradle.org/plugin/org.cyclonedx.bom gestellt; damit kann
  version_sync --update cyclonedx kuenftig automatisch anheben.
- Tests: TestPluginPortalResolution (Koordinaten, Resolver-Wahl je Eintrag, SKIP ohne
  Portal-Client, Modul-Subklasse inkl. Metadata-URL).
- OFFEN: Live-Aufloesung gegen plugins.gradle.org (kein Netz im Sandbox) - ein
  'version_sync --update'-Lauf auf Deiner Maschine verifiziert den Resolver real.
- Betroffene Repos: gradleInit (gradleInit.py, tools/version_sync.py, SSoT,
  test_gradleInit.py), gradleInitTemplates (5 Katalog-URLs),
  gradleInitModules (neuer Resolver, MODULES.toml).

v0056: ktor ohne explizites Shadow-Plugin + CycloneDX-SBOM in allen Templates

- Erkenntnis aus GMBooking/CoFix: das Ktor-Gradle-Plugin (io.ktor.plugin) bringt Shadow
  bereits eingebettet mit (CoFix nutzt tasks.shadowJar ohne Shadow im plugins-Block).
  ktor-Template entsprechend umgestellt: standalone verliert alias(libs.plugins.shadow);
  die Subproject-Variante ersetzt shadow durch alias(libs.plugins.ktor) (behaelt damit
  tasks.shadowJar und EngineMain); shadow komplett aus dem ktor-Katalog entfernt.
  Ein ktor-only-Multiproject ist damit shadow-frei.
- CycloneDX (3.3.0) nach dem GMBooking/CoFix-Muster in alle 5 Template-Kataloge und die
  SSoT aufgenommen (cyclonedx + Plugin cyclonedx-bom); alle 10 Build-Dateien wenden
  alias(libs.plugins.cyclonedx.bom) an und konfigurieren tasks.cyclonedxDirectBom
  bewusst auf runtimeClasspath (SBOM = "was laeuft in Produktion", nicht Test-Frameworks/
  Kover-Agent); kotlin-multi lib als Component.Type.LIBRARY, alle anderen APPLICATION.
  SSoT-URL auf mvnrepository (org.cyclonedx/cyclonedx-gradle-plugin), damit
  version_sync --update die Version auflosen kann (statt plugins.gradle.org).
- Verifiziert: Generierungsmatrix inkl. ktor-only-Multiproject (shadow weg, ktor/kover/
  cyclonedx aufgeloest), alle libs.*-Referenzen loesen auf, Suite 135 passed,
  version_sync --check gruen, alles LF.
- OFFEN: Gradle-Builds der generierten Projekte (kein Gradle/Netz im Sandbox), inkl.
  cyclonedxDirectBom-Task-Name gegen 3.3.0 und ktor buildFatJar/shadowJar.
- Betroffene Repos: gradleInitTemplates (ktor-Umbau, Kataloge, 10 Build-Dateien),
  gradleInit (SSoT).

v0055: Kover-Coverage-Gate in den Templates

- Kover (0.9.9) in alle 5 Template-Kataloge und die SSoT aufgenommen ([versions] +
  [plugins], Policy @* in der SSoT); multiproject-root bleibt minimal, kover kommt dort
  per Subprojekt-Merge an. Alle 10 Build-Dateien (build.gradle.kts + .subproject bzw.
  app/lib) wenden alias(libs.plugins.kover) an.
- Gate-Design (Ratchet, Boden 50, "test finalizedBy koverVerify"): Verify-Regel nur dort,
  wo Tests existieren, damit frisch generierte Projekte gruen bauen. Excludes sind der
  projektspezifische Teil und nutzen {{ group }}:
  * kotlin-single: Gate, Exclude {{ group }}.MainKt (Entry-Point-Wiring)
  * ktor: Gate ohne Excludes; NEU ApplicationTest.kt (testApplication, / und /hello) -
    module() wird von den HTTP-Tests ausgefuehrt; standalone-Build bekam
    kotlin("test") + useJUnitPlatform()
  * springboot: Gate, Excludes ApplicationKt + {{ project_name | PascalCase }}Application;
    NEU HelloControllerTest.kt (Unit-Test ohne Spring-Kontext)
  * kotlin-multi: lib mit Gate + NEU GreeterTest.kt; app nur Reporting (Entry-Point) mit
    Kommentar zum spaeteren Aktivieren
  * kotlin-javaFX: nur Reporting; Gate-Kommentar verweist auf TestFX (Smoke-Tests allein
    tragen keinen Coverage-Boden)
- Damit werden die bisherigen Test-Kit-Orphans (junit/assertj im ktor-Katalog) erstmals
  referenziert.
- Verifiziert: init aller 5 Templates + multiproject-root mit 4 Subprojekten; alle
  libs.*-Referenzen loesen auf (inkl. kover), Excludes rendern mit group, neue Tests
  werden generiert, keine leeren Versionen; version_sync --check gruen; alles LF.
- OFFEN: Gradle-Builds der generierten Projekte (kein Gradle/Netz im Sandbox) - bitte je
  Template ./gradlew build laufen lassen; ebenso validatorfx 1.0.0 (Major) ungebaut.
- BEFUND (separat, vorbestehend): kotlin-javaFX Hint Zeile 58 hat einen verschachtelten
  Default ({{ group }}.MainKt im Hint-Default), der unrendered in die generierte Datei
  gelangt -> mainClass.set("{{ group }}.MainKt"). Fix ausstehend.
- Betroffene Repos: gradleInitTemplates (Kataloge, 10 Build-Dateien, 3 neue Tests),
  gradleInit (SSoT).

v0054: update_all_versions.sh auf version_sync umgebogen (ein Weg zur SSoT)

- Problem: das Script (v0050) rief 'gradleInit versions --update --latest' direkt auf den
  Template-Katalogen auf und umging damit die SSoT
  (gradleInit/versions/gradle/libs.versions.toml). Folge: Drift - Templates hatten
  logback 1.5.35 / spring-boot 4.1.0, die SSoT 1.5.34 / 4.0.6; 'version_sync --check' und
  zwei test_version_sync-Tests waren rot.
- Fix: update_all_versions.sh ist jetzt ein duenner Wrapper um tools/version_sync.py und
  faehrt die Sequenz --update (SSoT anheben, im Rahmen der Constraint je Eintrag) ->
  --apply (Templates, Tool-Defaults, READMEs schreiben) -> --check (verifizieren). Kein
  direkter Zugriff mehr auf Template-Kataloge, kein --latest-Force-Pfad.
  Optionen: --check (read-only), --yes, --include-recent. Guards: python-Interpreter,
  Vorhandensein des gradleInit-Nachbar-Repos, unbekannte Optionen.
- SSoT-Kommentar korrigiert: die per-Eintrag-Policy wird von --update sehr wohl konsumiert
  (run_update nutzt VersionManager.check_updates); der Hinweis "nur --check implementiert"
  war veraltet.
- Verifiziert: --check meldet die Drift; SSoT-Bump + --apply konvergiert auf gruen und
  haelt LF; Guards greifen. ('--update' braucht Maven-Central-Netz, im Sandbox blockiert.)
- Betroffene Repos: gradleInitTemplates (update_all_versions.sh),
  gradleInit (versions/gradle/libs.versions.toml Kommentar).

v0053: Zeilenenden immer LF (kein LF -> CRLF mehr beim Schreiben)

- Problem: nach 'versions --update' hatte gradle/libs.versions.toml CRLF statt LF.
  Ursache: Path.write_text() oeffnet im Textmodus; unter Windows uebersetzt Python dabei
  jedes '\n' zu '\r\n'. Das betraf nicht nur den versions-Update, sondern jede
  geschriebene Datei (Template-Rendering, settings/build.gradle.kts, Katalog-Merge,
  gradle.properties, Config, Compiled-Cache) - generierte Projekte waren unter Windows
  durchgehend CRLF.
- Fix: neuer Helper write_text_lf(path, content) schreibt Bytes mit LF (analog zur
  bestehenden _normalize_text_bytes-Konvention beim Signieren). Alle 25 Text-Schreibstellen
  darauf umgestellt. Bestehende CRLF-Dateien werden beim Rewrite auf LF normalisiert.
  Ausnahme: der Windows-.cmd-Shim wird bewusst explizit als CRLF geschrieben (Batch-
  Konvention), plattformunabhaengig statt vom Zufall abhaengig.
- Tests: TestLineEndings (Helper normalisiert; update_version haelt LF; CRLF-Eingabe wird
  zu LF; Quellcode-Guard: kein rohes write_text mehr im Code).
- Betroffenes Repo: gradleInit (gradleInit.py, test_gradleInit.py).

v0052: --latest (und --version_policy) explizit in der init/subproject-Hilfe

- Problem: 'gradleInit init -h' zeigte --latest nicht. Es gibt mehrere hartcodierte
  init-Hilfe-Bloecke; der fuer 'init -h' (ohne Projektname) gezeigte listete nur
  --group/--project-version/--gradle/--kotlin/--jdk/--interactive. Mit Template tauchte
  "latest" nur zufaellig im --version_policy-Hilfetext auf, nicht als eigenes Flag.
- Fix: --latest, --version_policy und --dry-run explizit in allen init-Hilfe-Bloecken
  ergaenzt (frueher No-Name-Block, generischer Block, Template-Pfad via "Common options")
  sowie in der subproject-Hilfe. Veralteter JDK-Hinweis "11, 17, 21" auf "24, 25" korrigiert.
- Reine Hilfe-/Print-Aenderung, keine Logikaenderung.
- Betroffenes Repo: gradleInit (gradleInit.py).

v0051: --version_policy wirkt jetzt (war wirkungslos) + bessere Hilfe

- Problem: --version_policy (automatisch aus dem {{ version_policy }}-Platzhalter erzeugt)
  wurde nach build_context bedingungslos aus --latest ueberschrieben (@* bzw. @pin) -> ein
  explizites --version_policy hatte keine Wirkung. Zudem war die Hilfe nur "Set
  version_policy" ohne erlaubte Werte.
- Fix: Praezedenz explizit --version_policy > --latest (@*) > Default (@pin), in init und
  subproject. Helper normalize_version_policy (akzeptiert @-Token plus freundliche Woerter
  pin/latest/minor/patch, mit/ohne @) und resolve_version_policy. Ungueltige Werte werden mit
  klarer Meldung abgelehnt (Exit 1) statt still in den Katalog geschrieben.
- Hilfe: --version_policy hat jetzt eine kuratierte Beschreibung (Quelle: get_arguments) und
  Metavar POLICY; nennt @pin/@*/@^/@~/Ranges und den Hinweis --latest = @*.
- Tests: TestVersionPolicyResolution (Normalisierung, Praezedenz, Alias, ungueltig).
- Betroffenes Repo: gradleInit (gradleInit.py, test_gradleInit.py).

v0050: update_all_versions.sh nutzt versions --latest (kein @pin-sed-Hack mehr)

- Problem: das alte update_all_versions.sh ersetzte per sed '@pin' durch '@*' in den
  Kommentarzeilen. In den Templates steht die Policy aber als '{{ version_policy }}', nicht
  '@pin' - das sed war ein No-op, der Tool-Lauf sah weiter "implicit pin" -> kein Update.
- Fix: Script auf 'gradleInit versions --update --latest --include-recent --yes' pro Template
  umgestellt, kein sed mehr. --latest erzwingt die neueste Version fuer literale Eintraege;
  Platzhalter (kotlin, jdk) bleiben unangetastet. Neu: PATH-Check fuer gradleInit, Guard auf
  Vorhandensein von '--latest' (>= 1.12.4), '--dry-run' (nur Vorschau), Zusammenfassung.
- Verifiziert mit Stub-gradleInit: alle 6 Templates werden mit korrekten Flags durchlaufen.
- Setzt gradleInit v0049 (versions --latest) voraus.
- Betroffenes Repo: gradleInitTemplates (update_all_versions.sh).

v0049: versions --latest (Force-Modus) zum Aktualisieren der Template-Kataloge

- Problem: 'gradleInit versions --update' auf einen rohen Template-Katalog meldet alle
  Libs als [PINNED] und aendert nichts. Ursache: die Policy steht dort als unrendered
  Platzhalter '{{ version_policy }}'; URL_PATTERN erfasst als Constraint nur literales
  '@...', also ist die Constraint None -> "implicit pin" -> kein Update.
- Fix: neues Flag 'versions --latest'. Es behandelt jeden URL-gestuetzten, literalen
  Eintrag als @* (ueberschreibt @pin/implicit-pin) und aktualisiert auf die neueste
  stabile Version. Eintraege mit Platzhalter-Wert ('{{ kotlin_version }}', JDK-Hint)
  werden als [TEMPL] uebersprungen und nie zu einem Literal umgeschrieben.
- Damit aktualisiert 'gradleInit versions --update --latest --include-recent' pro Template
  die literalen Lib-Versionen (shadow, clikt, ktor, logback, spring-boot, junit, assertj,
  mockk, javafx, ...) auf neueste, waehrend kotlin/jdk Platzhalter bleiben.
- Hinweis: kotlin/gradle/jdk sind Tool-Defaults (DEFAULT_PROJECT_DEFAULTS /
  DEFAULT_GRADLE_VERSION / JDK-Hint), kein Maven-Central-Lookup; sie werden ueber die
  gradleInit-Konstanten + version_sync gepflegt, nicht ueber 'versions'.
- Tests: TestVersionsForceLatest (ohne --latest literal=PINNED, Platzhalter=TEMPLATED;
  mit --latest literal=UPDATE, Platzhalter unangetastet inkl. Write-Back-Pruefung).
- Betroffenes Repo: gradleInit (gradleInit.py, test_gradleInit.py).

v0048: multiproject-root Katalog auf minimale Basis reduziert

- Problem: der multiproject-root-Katalog (gradle/libs.versions.toml) war ein statischer
  Superset mit Versionen/Libraries/Plugins fuer ALLE Subprojekt-Typen (ktor, springboot,
  JavaFX-Stack, clikt) - auch wenn das Projekt diese Typen nie nutzt. Folge: toter Ballast
  im Katalog (spring-boot, javafx, ...) und 'versions --update' prueft/aktualisiert Libs,
  die das Projekt nicht referenziert.
- Fix: Root-Katalog auf die universelle Basis reduziert (jdk, kotlin, kotlin-jvm-Plugin,
  Gradle-Policy-Kommentar). Die Subprojekt-Templates bringen ihre Eintraege per
  merge_versions selbst mit; _merge_toml_content fuehrt bereits alle Sektionen zusammen
  ([versions], [libraries], [plugins], [bundles]). Der Katalog enthaelt am Ende nur, was
  die hinzugefuegten Subprojekte tatsaechlich nutzen.
- Verifiziert: frisches multiproject-root + ktor + springboot + kotlin-javaFX + kotlin-single
  -> alle libs.*-Verweise loesen auf; ktor + 2x kotlin-single -> kein spring/javafx im
  Katalog. Subprojekt-Merge-Dateien sind selbst vollstaendig (auditiert).
- Keine Aenderung an gradleInit.py.
- Betroffenes Repo: gradleInitTemplates (multiproject-root/gradle/libs.versions.toml).

v0047: PyYAML als Pflicht-Dependency + Cache-Selbstheilung + Diagnose

- Ursache des "Template 'ktor' does not support subproject mode" trotz vorhandenem
  subproject_mode (Zeile 37 im installierten TEMPLATE.md): PyYAML war als OPTIONAL
  eingestuft und wurde nie installiert. Ohne PyYAML faellt _parse_metadata auf einen
  flachen Parser zurueck, der verschachtelte Bloecke (subproject_mode, requirements,
  arguments) nicht lesen kann -> subproject_mode wird zu einem leeren String (falsy).
  Es war NICHT der Cache und kein veraltetes Template.
- Fix: PyYAML ist jetzt Pflicht-Dependency (REQUIRED_PACKAGES); der bestehende
  check_and_install_dependencies()-Dialog installiert es wie toml/jinja2. Kein eigener
  YAML-Parser (PyYAML ist die robuste Standardloesung). REQUIRED_PACKAGES und
  OPTIONAL_PACKAGES als Modulkonstanten (testbar). CI installiert PyYAML bereits.
- Cache-Selbstheilung: der Compiled-Cache wird bei Tool-Versionswechsel automatisch neu
  gebaut (Versions-Stempel ~/.gradleInit/cache/.tool_version). Eine reine mtime-Pruefung
  kann Aenderungen an der Kompilierlogik selbst nicht erkennen.
- Diagnose: gradleInit --version zeigt jetzt Version, Python, YAML-Parser, Pfade und
  Cache-Status (und fuehrt dabei den Cache-Check aus). base_dir-Anlage robust (parents=True).
- Tests: TestDependenciesAndCache (PyYAML required; Cache-Rebuild bei Versionswechsel;
  kein Rebuild bei gleichem Stand).
- Betroffenes Repo: nur gradleInit (gradleInit.py, test_gradleInit.py).

v0046: Hint-Scanner liest jetzt gradle/libs.versions.toml

- Wurzelgrund aus v0044: der reiche jdk-Hint (Default 25, Regex (24|25)) steht in
  gradle/libs.versions.toml, aber _find_template_files schloss das gesamte Verzeichnis
  'gradle' aus -> der Hint wurde nie geparst (Default/Regex inert).
- Fix: exclude_dirs auf {.git, build, .gradle} reduziert; 'gradle' wird gescannt, nur
  gradle/wrapper (Binaries/generierte Properties) bleibt ausgeschlossen. Es werden ohnehin
  nur Textendungen gescannt (kein .jar). Damit liefert das Template fuer jdk_version jetzt
  Default 25 UND Regex (24|25); das Rendering laeuft unveraendert ueber _process_directory.
- Folge (beabsichtigt): die (24|25)-Validierung ist nun aktiv. --jdk-version 21/17 wird mit
  klarer Meldung abgelehnt (passt zur JDK-Basis >=24 aus v0041); 24/25 und der Default 25
  funktionieren. test_config_integration test_02 nutzte CLI --jdk_version 17 -> auf 24
  umgestellt (Testzweck 'CLI ueberschreibt Config' bleibt erhalten).
- Tests: neuer test_jdk_hint_in_catalog_is_scanned (prueft Default 25 + Regex 24|25 aus dem
  Katalog); erkennt eine Scanner-Regression (mit altem Ausschluss rot). kotlin_version hat
  weiterhin keinen Hint -> Default kommt aus Config/Fallback (DEFAULT_PROJECT_DEFAULTS).
- Betroffenes Repo: nur gradleInit (gradleInit.py, test_gradleInit.py,
  test_config_integration.py).

v0045: gradle_version ebenfalls absichern + Leerwert-Fall (blanke Config)

- Folge aus dem Hinweis "config hat auch gradle_version": get_config_default gibt einen
  im Config VORHANDENEN, aber leeren Wert zurueck (statt des Fallbacks). Damit brachen
  kotlin/jdk/gradle nicht nur bei FEHLENDEM Key, sondern auch bei leerem Wert
  ("Using Gradle version: " leer -> gradle wrapper --gradle-version "" wuerde scheitern;
  kotlin/jdk wieder leer im Katalog, vom Guard abgefangen).
- Fix: der Fallback (init + subproject) deckt jetzt kotlin_version, jdk_version UND
  gradle_version ab und ist robust gegen leere Werte
  (... or DEFAULT_PROJECT_DEFAULTS[key]). Zusaetzlich faengt die Gradle-Aufloesung im
  init-Pfad einen leeren Wert ab (gradle_version = DEFAULT_GRADLE_VERSION), damit auch
  Ausgabe und Wrapper-Aufruf stimmen.
- Tests: TestStaleConfigGeneration deckt jetzt beide Faelle ueber alle fuenf Templates ab -
  'strip' (Key fehlt) und 'blank' (Key leer) -, prueft keine leeren Katalog-Versionen und
  verifiziert die aufgeloeste Gradle-Version aus der Ausgabe. Neuer Test prueft kotlin/jdk/
  gradle gegen die verwalteten Defaults (DEFAULT_PROJECT_DEFAULTS) statt Hartkodierung.
  Nachgewiesen: bei deaktiviertem Fix werden strip und blank rot.
- Betroffenes Repo: nur gradleInit (gradleInit.py, test_gradleInit.py).

v0044: Erweiterung von v0043 - jdk-Version ebenfalls absichern + E2E-Tests

- jdk brach im selben Stale-Config-Szenario wie kotlin (jdk = "" -> ungueltiger
  Katalog, vom Guard aus v0043 abgefangen). Ursache: der jdk-Hint mit Default 25
  steht in gradle/libs.versions.toml, aber der Hint-Scanner schliesst das Verzeichnis
  'gradle' aus -> dieser Default wird nie geparst; nur die nackten {{ jdk_version }}
  (README) zaehlen, ohne Default. Frische Configs setzen jdk_version (25), aeltere nicht.
- Fix: init- und subproject-Fallback deckt jetzt kotlin_version UND jdk_version ab
  (Quelle: DEFAULT_PROJECT_DEFAULTS, also weiterhin eine verwaltete Stelle).
- Neue E2E-Tests TestStaleConfigGeneration in test_gradleInit.py: erzeugen ueber den
  echten CLI-Pfad (Subprozess; HOME mit Config ohne kotlin/jdk/gradle) fuer alle fuenf
  Templates und pruefen, dass der Katalog keine leeren Versionen hat und kotlin/jdk auf
  die Defaults fallen. Die bisherigen Generierungstests bauen den Context von Hand und
  konnten den Fehler daher nicht sehen. Nachgewiesen: bei deaktiviertem Fallback werden
  die Tests rot (['jdk', 'kotlin'] pro Template).
- Offen/Hinweis: der reiche jdk-Hint in libs.versions.toml ist wegen des 'gradle'-
  Ausschlusses im Hint-Scanner inert (Regex/Default werden nicht angewendet). Funktional
  ueber Config-Default + Fallback + Guard abgedeckt; echtes Parsen dieser Hints waere ein
  separater Schritt.
- Betroffenes Repo: nur gradleInit (gradleInit.py, test_gradleInit.py).

v0043: Fix - leere kotlin-Version im generierten Katalog (unvollstaendiges Projekt)

- Symptom: `init` mit einer aelteren Config (ohne kotlin_version) erzeugte
  gradle/libs.versions.toml mit `kotlin = ""`. Gradle lehnt den Katalog ab
  ("Empty version for plugin alias 'kotlin'"), `gradle wrapper` schlaegt fehl,
  daher fehlen gradlew/gradlew.bat/gradle/wrapper/*. Das Tool meldete trotzdem
  "Project created successfully" und committete das unvollstaendige Projekt.
- Ursache: Alle Templates fuehren `kotlin = "{{ kotlin_version }}"` ohne Default.
  ContextBuilder liefert fuer eine Variable ohne Quelle einen leeren String.
  Frische Configs setzen kotlin_version (2.4.0), aeltere Configs nicht -> leer.
  --latest ist nicht die Ursache (setzt nur version_policy).
- Fix (nur gradleInit, Templates unveraendert -> keine verstreuten Versionen):
  * DEFAULT_PROJECT_DEFAULTS als einzige Quelle der Config-Defaults; das Literal
    'kotlin_version': '2.4.0' bleibt dort erhalten (version_sync verwaltet es weiter).
  * init- und subproject-Ablauf: kotlin_version faellt auf den Config-Default bzw.
    DEFAULT_PROJECT_DEFAULTS['kotlin_version'] zurueck, falls leer.
  * Guard find_empty_catalog_versions: nach dem Rendern wird gradle/libs.versions.toml
    auf leere [versions]-Eintraege geprueft; bei Fund bricht generate() mit klarer
    Fehlermeldung ab - kein Wrapper, kein Git-Commit, kein falsches "success".
- Tests: neue TestCatalogGuard (4) in test_gradleInit.py. version_sync --check gruen,
  genau ein verwaltetes kotlin-Literal in gradleInit.py. Verbleibende Suite-Fehler nur
  umgebungsbedingt (Gradle-Builds ohne Gradle, test_cli-Isolation, test_real_compilation).
- Betroffenes Repo: nur gradleInit (gradleInit.py, test_gradleInit.py).

v0042: CI-Release-Fix (test_gradleInit.py) und TODO.md-Bereinigung

- Release-Workflow lief auf Tag v1.12.0 rot: test_gradleInit.py hatte zwei
  vorbestehende Test-Altlasten (unabhaengig vom v1.12.0-Inhalt; der Workflow
  fuehrt nur test_gradleInit.py aus).
- test_ktor_generation: pruefte veraltet 'embeddedServer'/'Netty' in Application.kt.
  Das ktor-Template nutzt das EngineMain-Muster (fun Application.module() +
  application.yaml), kein embeddedServer mehr. Assertion auf 'fun Application.module()'
  und 'routing' umgestellt.
- test_generation_speed (TestPerformance): baute einen Minimalkontext ohne die
  Feature-Flags und scheiterte an 'enable_clikt is undefined' (StrictUndefined).
  Kontext um enable_clikt/enable_shadow/enable_detekt/enable_dokka/enable_kover,
  version_policy und optionale Felder ergaenzt (analog zu _generate_project);
  jdk_version auf 25 angehoben.
- Verifikation: beide Tests lokal gruen; voller test_gradleInit.py-Lauf nur mit den
  vier gradle_build-Tests rot (Sandbox ohne Gradle; in der CI gruen).
- docs/TODO.md: interne Arbeitsdoku-Verweise aus den 'Betroffenes Repo'-Zeilen
  entfernt; TODO.md wird als getrackter, oeffentlicher Snapshot gefuehrt.
- Betroffenes Repo: nur gradleInit (test_gradleInit.py, docs/TODO.md).

v0041: JDK-Basis >= 24, Spring Boot 4.0.6, Virtual Threads, Resolver-Pre-Release-Fix

- gradleInitModules (Wurzelfix): MavenCentralResolver._is_prerelease nutzte eine
  Substring-Liste mit nur m1/m2/m3 -> Milestones wie 4.1.0-M4 galten faelschlich als
  stabil und wurden als latest zurueckgegeben. Folge: version_sync erhielt 4.1.0-M4,
  der is_stable-Backstop (v0037) lehnte ab und blieb auf 4.0.2 -> 4.0.6 wurde verschluckt.
  Ersetzt durch delimiter-verankerte Regex (_PRERELEASE_RE), erkennt jedes M<n>, RC, ea,
  dotted M1, milestone; stabile Versionen (4.0.6, 26.0.1, 1.2.3.RELEASE) bleiben stabil.
  Neuer Test resolvers/test_maven_central.py (standalone, ohne Netzwerk/Dependencies).
- gradleInit SSoT: spring-boot 4.0.2 -> 4.0.6 (per --apply in Templates + README
  propagiert). _create_default_config: jdk_version '21' -> '25' (war unter dem neuen
  (24|25)-Floor sogar ungueltig), gradle_version Literal '9.3.1' -> DEFAULT_GRADLE_VERSION.
  README-Prerequisite JDK 21+ -> 24+. test_version_sync: zwei veraltete Testdaten
  (kotlin 2.3.10 / junit 5.13.4) drift-fest gemacht (lesen jetzt aus der SSoT).
- gradleInitTemplates: JDK-Basis ueberall auf >= 24 vereinheitlicht. springboot-Hint
  (21|24|25)=24 -> (24|25)=25; multiproject-root/gradle.properties zweiter jdk-Hint
  (11|17|21|23)=21 -> (24|25)=25 (war Konflikt mit der libs.versions.toml). Alle
  TEMPLATE.md jdk: ">=21" -> ">=24"; TEMPLATE_GUIDE.md ">=17" -> ">=24"; README/Help-
  Texte (default 23/min 21 -> 25/24, --config jdk_version, Kommentare) angeglichen.
  Hartkodierte Prosa-Staende korrigiert: JUnit 5 -> JUnit 6, JavaFX 25 -> 26,
  JavaFX 25.0.1 -> 26.0.1, ControlsFX 11.2.2 -> 11.2.3. springboot application.properties:
  spring.threads.virtual.enabled=true ergaenzt (JDK 21+, empfohlen fuer 24/25).
- Verifikation: version_sync --check sauber; lokale End-to-End-Generierung (springboot,
  kotlin-single) ok; keine neuen Testfehler ggü. unveraendertem Upload (Baseline-Vergleich).
- Offen/angemerkt: (a) --jdk-version/--config werden NICHT gegen den (24|25)-Hint
  validiert (jdk_version=21 erzeugt still jdk="21") - vorbestehend, separater Tool-Fix
  auf Zuruf. (b) Prosa-Versionen in TEMPLATE.md/README/ADVANCED sind nicht <!--v-->-
  annotiert und driften daher; spaeter annotieren/platzhaltern. (c) Remote-Klon-Tests
  scheitern an enable_clikt (Test-Harness umgeht CLI-Default-Injektion) - vorbestehend.

v0040: Zeilenende-unabhaengige Signatur-Verifikation (Wurzelfix)

- Ziel: CRLF/LF darf die Repo-Verifikation grundsaetzlich nicht mehr brechen,
  unabhaengig von Working-Copy, core.autocrlf oder Plattform.
- Neuer Helper _normalize_text_bytes(data): kollabiert CRLF/CR zu LF fuer
  Textdateien; Binaerdateien (enthalten ein NUL-Byte, z.B. gradle-wrapper.jar)
  bleiben unveraendert (kein Korrumpieren).
- Angewandt in: RepositorySecurity._get_file_hash (Einzel-Datei-Hash),
  sign_repository + verify_repository (CHECKSUMS-Bytes vor Signatur und Parsing),
  und _verify_single_file (Self-Update: script_bytes und checksums_bytes).
- Damit sind Einzel-Hashes UND die Signatur ueber die CHECKSUMS-Datei selbst
  zeilenende-invariant.
- Kompatibilitaet: fuer bereits als LF committete Dateien ist der neue Hash
  identisch (Normalisierung ist No-Op) - bestehende Signaturen ueber LF-Inhalte
  bleiben gueltig. Nur bewusst als CRLF committete Dateien (z.B. gradlew.bat mit
  eol=crlf) bekommen einen neuen Hash und erfordern ein einmaliges Neu-Signieren.
  Verifizier-Tool (CI/Clients/Self-Update) muss >= v0040 sein.
- Tests (TDD): TestLineEndingNormalization (normalize, NUL-Binary, _get_file_hash
  CRLF==LF, sign/verify-Roundtrip ueber eine CRLF-Working-Copy) und zwei neue
  Faelle in TestVerifySingleFile (CRLF-Script, CRLF-Checksums verifizieren).
- Betroffenes Repo: nur gradleInit (gradleInit.py, test_self_update.py).

v0039: Fix CRLF der SSoT-libs.versions.toml bei version_sync --update

- Restluecke aus v0038: die SSoT-Lib-Werte werden ueber VersionManager.update_version
  (gradleInit.py) geschrieben, das write_text nutzt -> CRLF auf Windows. Damit war
  versions/gradle/libs.versions.toml im signierten gradleInit-Repo weiterhin CRLF-faehig.
- Loesung: run_update normalisiert die SSoT-Catalog-Datei nach den Lib-Updates per
  _write_lf erneut auf LF (lokalisiert in version_sync; End-User-Pfad versions --update
  bleibt unveraendert).
- Test (TDD): test_run_update_ssot_toml_is_lf (FakeMaven erzwingt ein Lib-Update,
  prueft mockk -> 1.1.0 und kein \r in der SSoT-toml); deckt zugleich den Lib-Pfad in
  run_update ab, den der bisherige Test nicht traf.
- Betroffenes Repo: nur gradleInit (tools/version_sync.py, Test).

v0038: Fix CRLF beim Schreiben in version_sync (signaturrelevant)

- Problem: version_sync --apply/--update schrieb mit Path.write_text, das auf
  Windows '\n' zu CRLF uebersetzt. Da _get_file_hash ueber rohe Bytes hasht und
  git committete Dateien auf LF normalisiert, wuerde eine CRLF-Working-Copy nach
  dem Signieren auf einem frischen Clone / im CI nicht mehr verifizieren
  (Hash ueber LF != CHECKSUMS ueber CRLF).
- Loesung: Helper _write_lf(path, text) normalisiert auf LF und schreibt rohe
  Bytes (write_bytes) - plattformunabhaengig. Alle 4 Schreibstellen (Template-
  TOMLs, Tool-Defaults, READMEs, SSoT-wrapper.properties) nutzen ihn.
- Test (TDD): TestWriteLf (CRLF/CR -> LF); run_update-Test prueft zusaetzlich, dass
  die wrapper.properties kein \r enthaelt.
- Hinweis: betrifft nur version_sync (das die signierten Repos editiert). Der
  End-User-Pfad (versions --update auf einem generierten Projekt) ist nicht
  signaturrelevant fuer gradleInit und bleibt unveraendert.
- Betroffenes Repo: nur gradleInit (tools/version_sync.py, Test).

v0037: Fix Pre-Release-Versionen bei Lib-Updates (Milestone/RC ausschliessen)

- Problem: version_sync --update (und versions --update) schlug fuer spring-boot
  4.0.2 -> 4.1.0-M4 vor. 4.1.0-M4 ist ein Milestone; @^ erlaubt numerisch 4.1.0,
  aber ein stabiler Wartungs-Bump darf kein M/RC/alpha/beta/SNAPSHOT waehlen
  (analog zum Gradle-Nightly-Fix v0034).
- Loesung: neuer Helper VersionConstraintChecker.is_stable(version) (lehnt
  Pre-Release-Qualifier ab: -M\d, -RC, -alpha, -beta, -SNAPSHOT, -milestone, -pre,
  -dev, -ea, -cr). In VersionManager.check_updates wird ein als beste Uebereinstimmung
  gefundener Pre-Release zurueckgewiesen -> Status CURRENT mit Hinweis
  ("newest match X is a pre-release; staying on Y").
- Gilt fuer den End-User-Befehl und version_sync gleichermassen (beide nutzen
  check_updates).
- Hinweis: findet die Aufloesung nur einen Pre-Release als hoechste Uebereinstimmung,
  bleibt der Eintrag konservativ auf der aktuellen Version. Wer bewusst Milestones
  ziehen will, muss das manuell tun (derzeit kein Opt-in-Flag).
- Test (TDD): TestIsStable (stabile inkl. .RELEASE/.Final akzeptiert,
  Pre-Releases abgelehnt).
- Betroffenes Repo: nur gradleInit (gradleInit.py, Test).

v0036: Fix bloesses @^/@~ im Lib-Pfad + transparente Anzeige in version_sync --update

- Problem: version_sync --update fand keine Lib-Updates, nur Gradle. Ursache: die
  SSoT nutzt durchgaengig bloesses @^ (ohne Basisversion). satisfies(x, '^') ist
  immer False -> VersionManager.check_updates wertete jeden @^-Eintrag als
  VIOLATE/CURRENT, nie als UPDATE. (Derselbe Caret-ohne-Basis-Fall wie zuvor bei
  Gradle.)
- Loesung: neuer Helper VersionConstraintChecker.anchor(constraint, current) -
  bloesses '^'/'~' wird an die aktuelle Version verankert ('^' -> '^9.3.1').
  check_updates verankert vor der Auswertung; _select_gradle_target nutzt denselben
  Helper (Vereinheitlichung).
- Transparenz: version_sync run_update zeigt jetzt ALLE Status (UPDATE/RECENT/
  CURRENT/PINNED/SKIP/VIOLATE) plus eine Summary-Zeile - nicht mehr nur UPDATE.
  Dadurch ist sichtbar, dass und wie die Libs geprueft wurden.
- Q2 (keine Template-Aenderung bei reinem Gradle-Bump) ist erwartet: Templates
  tragen keine statische Gradle-Version; die einzige abgeleitete Stelle ist
  DEFAULT_GRADLE_VERSION in gradleInit.py.
- Test (TDD): TestConstraintAnchor (bloesses caret/tilde verankert, andere
  Constraints unveraendert, anschliessend satisfies).
- Betroffenes Repo: nur gradleInit (gradleInit.py, tools/version_sync.py, Tests).
- Folge: ein erneutes version_sync --update findet jetzt die @^-Lib-Updates; das
  anschliessende --apply aendert dann auch gradleInitTemplates.

v0035: version_sync --update implementiert

- version_sync.py --update hebt die SSoT-Versionen ueber die Resolver: Libs via
  MavenCentral/VersionManager innerhalb des Maintenance-Constraints (@^ etc.),
  Gradle via services.gradle.org gemaess "# gradle @..."-Kommentar. Schreibt NUR
  die SSoT-Dateien; Propagation bleibt getrennt (--apply danach).
- Honoriert die 48h-"too recent"-Schwelle (gegen das Maven-Central-Download-Problem);
  --include-recent ueberschreibt sie. --yes ueberspringt den Bestaetigungs-Prompt.
- Wiederverwendung: version_sync importiert gradleInit als Library (Import ist
  nebenwirkungsfrei genug - check_and_install_dependencies ist bei vorhandenen Deps
  ein stummes No-op). Reine, testbare gradle_ssot_plan(gi, toml_text, wrapper_text,
  available).
- Bugfix nebenbei: _select_gradle_target verankert bloesses @^ / @~ (ohne Basis,
  wie die SSoT es nutzt) an der aktuellen Version - sonst matcht das Caret nichts.
- Test (TDD): TestUpdateMode (gradle_ssot_plan: caret/pin/keine-Policy; run_update
  schreibt nur die SSoT-wrapper.properties via injiziertem gi + maven_central=None);
  test_gradle_update um bare-caret erweitert.
- Betroffenes Repo: nur gradleInit (tools/version_sync.py, gradleInit.py, Tests).
- Damit sind --check / --apply / --update alle implementiert.

v0034: Fix Gradle-Versionsfilter (Nightly/RC schluepften durch)

- Problem: versions --update schlug fuer Gradle eine Nightly vor
  (9.7.0-20260602012325+0000). fetch_gradle_versions filterte nur per String-Match
  auf "nightly"/"rc" - eine Nightly heisst aber 9.7.0-<timestamp>+0000 ohne das Wort
  "nightly", rutschte also durch.
- Loesung (Wurzel): Filterung ueber die Metadaten-Flags der /versions/all-Eintraege
  (snapshot, nightly, releaseNightly, rcFor, activeRc, milestoneFor, broken) statt
  String-Match. Ausgelagert in testbares _filter_gradle_versions(data, ...).
- Zweite Schutzschicht: _select_gradle_target beruecksichtigt nur finale Versionen
  (Regex ^\d+\.\d+(\.\d+)?$); rc/nightly/milestone-Formen werden ignoriert, selbst
  wenn sie doch in der Liste landen.
- Nebeneffekt: auch die Gradle-Wahl bei der Projektgenerierung zieht keine Nightlies
  mehr.
- Test (TDD): TestFilterGradleVersions (Default schliesst Nightly/RC/Milestone/broken
  aus; include_nightly/include_rc), TestSelectTarget.test_ignores_nightly_and_rc.
- Betroffenes Repo: nur gradleInit (gradleInit.py, Test).

v0033: gradleInit --update all (Tool + Templates + Module)

- Neues "all"-Ziel fuer das globale --update: "gradleInit --update all" (auch ALL,
  case-insensitiv) aktualisiert in einem Lauf gradleInit selbst, die Template-Repos
  und die Module.
- Dispatch-Helper _is_self_update_request -> _self_update_target(update_flag, command):
  command None -> 'self', command 'all' -> 'all', sonst None (templates/modules/
  versions behalten ihr eigenes --update). --update bleibt store_true; 'all' kommt als
  Positional-Token, daher keine riskante Parser-Aenderung.
- handle_update_all: ruft handle_self_update(), dann repo_manager.ensure_official_
  templates() + update_all(), dann module_loader.update_modules(); jeweils mit eigener
  Sektion; Sammel-Exitcode (1, falls ein Schritt fehlschlaegt).
- Test (TDD): TestSelfUpdateTarget (self/all/ALL/None inkl. kein Kapern von
  templates/modules/versions).
- Betroffenes Repo: nur gradleInit (gradleInit.py, Test).

v0032: Gradle-Policy-Parser streng gemacht

- GRADLE_POLICY_RE auf genau eine kanonische Form: ^\s*#\s*gradle\s+@(.+?)\s*$
  (Leerzeichen vor @ verpflichtend, kein =-Toleranz mehr). Konsistent mit den
  Lib-Kommentaren (Space + @-Marker). Abweichende Schreibweisen (# gradle = @*,
  # gradle@*, # gradle pin) werden bewusst als "keine Policy" behandelt -> kein
  Gradle-Update, keine Fehlermeldung.
- Test (TDD) angepasst: strenge Ablehnung der Nicht-kanonischen Formen statt
  =-Toleranz.
- Betroffenes Repo: nur gradleInit (gradleInit.py, Test). Templates und
  SSoT bleiben unveraendert (ihr Format "# gradle ... @..." erfuellt die strenge
  Regel bereits).

v0031: Gradle-Update in versions --update (End-User)

- versions --update aktualisiert jetzt auch die Gradle-Wrapper-Version. Policy steht
  als Kommentar in libs.versions.toml im selben Muster wie die Lib-Constraints
  (@-Marker am Ende, kein =): "# gradle @pin" / "# gradle @*" / "# gradle @<10.0.0".
  Der Wert lebt weiter in gradle/wrapper/gradle-wrapper.properties (distributionUrl).
- Mechanik: Policy aus dem Kommentar lesen, aktuelle Version aus distributionUrl,
  Kandidaten via fetch_gradle_versions() (services.gradle.org, nur Stable), hoechste
  Version waehlen, die die Policy erfuellt und neuer ist (VersionConstraintChecker).
  Bei Anwendung wird NUR der distributionUrl umgeschrieben (kein erneutes
  "gradle wrapper"). pin -> kein Update. Gradle erscheint in der UPDATE/PINNED/
  CURRENT-Anzeige und im gemeinsamen "Apply updates?"-Fluss.
- Helfer (testbar): _parse_gradle_policy (tolerant ggue = ; kein Fehlmatch auf
  Lib-Zeilen oder den Erklaer-Kommentar), _extract_gradle_version,
  _rewrite_distribution_url (nur Version, escaped Doppelpunkt bleibt),
  _select_gradle_target.
- Templates: in allen 6 libs.versions.toml den Kommentar "# gradle {{ version_policy }}"
  ergaenzt (ohne --latest -> @pin, mit --latest -> @*, wie die Lib-Constraints).
- SSoT-Kommentar (versions/gradle/libs.versions.toml) auf das kanonische Format
  "# gradle @^" gebracht.
- Test (TDD, neu): test_gradle_update.py (Policy-Parsing, Versions-Extraktion/Rewrite,
  Zielauswahl inkl. @*, @<10.0.0, @^, @pin, kein-neueres).
- Betroffene Repos: gradleInit (gradleInit.py, neuer Test, SSoT-Kommentar),
  gradleInitTemplates (6 libs.versions.toml).
- Offen/parkt: dieselbe Mechanik fuer version_sync --update (SSoT-Wrapper).

v0030: Fix Regression aus v0029 - globales --update kaperte Subcommand-Updates

- Problem: Das in v0029 eingefuehrte Top-Level-Flag --update wurde im Phase-1-Parser
  fuer JEDE Eingabe mit --update ausgewertet, also auch fuer "templates --update",
  "modules --update" und "versions --update". Es rief handle_self_update() und kehrte
  vorzeitig zurueck, bevor das eigentliche Subcommand lief. Folge: das Template-Cache
  wurde nie aktualisiert (alte ktor-Templates mit minOf(jdk,24) -> JDK-25-Build brach
  erneut) und versions --update lief nicht (shadow blieb 9.3.1 trotz @*).
- Loesung: neuer Helper _is_self_update_request(update_flag, command) -> nur
  Selbst-Update, wenn KEIN Subcommand vorliegt (command is None). Subcommands haben
  ihr eigenes --update. Phase-1-Dispatch nutzt diesen Helper.
- Test (TDD, erweitert): test_self_update.py um TestSelfUpdateRequest (update ohne
  command -> True; update mit templates/modules/versions/init -> False).
- Betroffenes Repo: nur gradleInit (gradleInit.py, Test).
- Wichtig fuer die Wiederherstellung: nach Update des Tools muss "templates --update"
  erneut laufen, damit das Cache die korrigierten Templates (Toolchain-Fix v0027)
  zieht. Voraussetzung: die korrigierten Templates sind tatsaechlich nach GitHub
  gepusht. Achtung: der separate CHECKSUMS-Stolperstein bei templates --update kann
  dabei erneut auftreten (lokal modifizierte CHECKSUMS.sha256 -> git pull bricht).

v0029: gradleInit --update (Selbst-Update)

- Neues Top-Level-Flag --update (im Phase-1-Parser, vor dem Subcommand-Dispatch).
- detect_install_type: ist gradleInit.py in einem Git-Working-Tree
  (git rev-parse --is-inside-work-tree)? -> Git-Modus, sonst Single-File-Modus.
- Git-Modus: git pull --ff-only im Repo-Top-Level; niemals force/reset; bei lokalen
  Aenderungen oder Divergenz sauberer Abbruch mit Hinweis.
- Single-File-Modus: neuestes Release-Tag (vX.Y.Z) ueber die GitHub-API ermitteln,
  gradleInit.py + CHECKSUMS.sha256 + CHECKSUMS.sig vom Tag laden, Signatur ueber die
  rohen CHECKSUMS-Bytes mit dem eingebetteten OFFICIAL_PUBLIC_KEY pruefen, dann den
  SHA-256 der geladenen Datei gegen den CHECKSUMS-Eintrag abgleichen. Nur bei Erfolg
  atomarer Ersatz (temp schreiben, Modus uebernehmen, alte Version als .bak sichern,
  os.replace). Bei ungueltiger/fehlender Signatur: Abbruch (kein --force).
- Self-Repo-Konstanten ergaenzt (SELF_REPO, SELF_REPO_SLUG).
- Test (TDD, neu): test_self_update.py - _select_latest_tag (hoechstes Semver),
  detect_install_type (git vs single-file), _verify_single_file (gueltig, falsche
  Signatur, manipuliertes Script, fehlender Eintrag). Netzwerk/git-pull/Replace sind
  duenne Wrapper, vom CI verifiziert.
- Betroffenes Repo: nur gradleInit (gradleInit.py, neuer Test).

Reihenfolge der naechsten Schritte (mit Urs abgestimmt)

1. (erledigt in v0026) version_sync --apply
2. (erledigt in v0028) gradle-wrapper.jar Fix
3. (erledigt in v0029) gradleInit --update Selbst-Update

v0028: Fix gradle-wrapper.jar wird git-ignoriert (.gitignore-Reihenfolge)

- Problem: In 5 Templates stand die Ausnahme !gradle/wrapper/gradle-wrapper.jar
  VOR der breiten *.jar-Regel. In .gitignore gewinnt das letzte passende Muster,
  also hat *.jar die Ausnahme wieder aufgehoben -> die Wrapper-JAR war ignoriert
  und git add . liess sie aus (genau das beobachtete Symptom). Die Wrapper-JAR
  gehoert nach Gradle-Empfehlung ins Repo.
- Loesung: in kotlin-single, kotlin-multi, ktor, springboot, kotlin-javaFX die
  Negation hinter *.jar verschoben (mit Kommentar "must be after *.jar"), analog
  zu multiproject-root, das bereits korrekt war. Root-Cause-Fix statt git add -f.
- Test (TDD, neu): test_wrapper_gitignore.py prueft mit git check-ignore (Ground
  Truth) je Template, dass gradle/wrapper/gradle-wrapper.jar NICHT ignoriert wird.
- Betroffene Repos: gradleInitTemplates (5 .gitignore), gradleInit (neuer Test).

v0027: Fix JVM-Toolchain (JDK-25-Build)

- Problem: generierte Projekte setzten jvmToolchain(minOf(jdk, 24)). jvmToolchain
  legt das TOOLCHAIN-JDK fest (welches JDK Gradle sucht). Mit JDK 25 ausgewaehlt
  verlangte der Build damit ein installiertes JDK 24 -> "Cannot find a Java
  installation matching languageVersion=24". Der Cap sass am falschen Hebel.
- Hintergrund: Der 24er-Cap war fuer Kotlin <= 2.2 korrekt (max Java-24-Bytecode).
  Kotlin 2.3.0 (Dez 2025) bringt Kotlin/JVM-Support fuer Java 25. Die SSoT pinnt
  Kotlin 2.3.10 (>= 2.3.0), GMBooking lief via --latest auf 2.4.0 - beide koennen
  25er-Bytecode. Maximal waehlbares JDK ueber alle Templates ist 25. Der Cap ist
  damit obsolet und wurde ersatzlos entfernt.
- Loesung: in allen 8 Toolchain-Stellen jvmToolchain(minOf(<jdk>, 24)) ->
  jvmToolchain(<jdk>). Betroffen: kotlin-single, ktor, springboot, kotlin-javaFX
  (build.gradle.kts) sowie kotlin-multi und multiproject-root (buildSrc/build.gradle.kts
  und buildSrc kotlin-common-conventions.gradle.kts; deckt die Subprojekte ueber die
  Conventions ab). Veraltete "max JDK 24"-Kommentare aktualisiert.
- Toolchain == ausgewaehltes JDK; Java- und Kotlin-Bytecode-Target damit konsistent.
- Test (TDD, neu): test_toolchain.py - kein Build-File darf jvmToolchain(minOf(...))
  verwenden; jede jvmToolchain-Stelle referenziert das JDK.
- Betroffene Repos: gradleInitTemplates (8 Build-Files), gradleInit (neuer Test).
- Hinweis (CHECKSUMS): nach Aenderungen in beiden Repos neu signieren (sign.sh).

v0026: version_sync.py --apply

- --apply schreibt die SSoT-Werte in alle abgeleiteten Ziele: Template-TOML-Werte
  ([versions], nur Werte-Zeilen; Jinja-Platzhalter wie kotlin und jdk bleiben),
  Tool-Defaults (kotlin_version, DEFAULT_GRADLE_VERSION; Variante A) und die
  README-Marker (Span-Werte + generierter Block, formaterhaltend). Beachtet
  Overrides. Nach dem Schreiben laeuft intern --check; verbleibende Drift -> Exit 1.
- Idempotent: auf einem konsistenten Baum aendert --apply nichts.
- Tests (TDD, erweitert): test_version_sync.py um Apply-Funktionen plus Roundtrip
  (SSoT-Bump -> run_apply -> run_check muss 0 sein; Wert ist in den Template-
  Katalogen angekommen). Gesamt 14 Tests gruen.
- Diese Lieferung aendert nur das gradleInit-Repo; gradleInitTemplates unveraendert
  seit v0025.

In Planung (Design abgestimmt, noch nicht umgesetzt)

- version_sync --update: SSoT-Versionen im Rahmen der Maintenance-Constraints
  hochziehen (VersionManager fuer Maven Central; fetch_gradle_versions fuer Gradle).
  Voraussetzung: Top-Level-Aufruf check_and_install_dependencies() in gradleInit.py
  in den __main__-Guard verschieben (Import als Library ohne Seiteneffekt).
- Gradle-Maintenance-Meta auch in die Template-libs.versions.toml spiegeln.
- Offene Entscheidung: per-Library Maintenance-Constraint im SSoT (aktuell Default @^).
  Offene Folgefrage: ob End-User-"gradleInit versions --update" Gradle mitzieht.
- templates --update bricht bei lokal modifizierter CHECKSUMS.sha256 (Verify-/
  Normalisierungspfad verschmutzt den Cache-Working-Tree). Ursache noch offen.

v0025: Versions-SSoT Bootstrap + version_sync.py --check

- SSoT (neu): gradleInit/versions/gradle/libs.versions.toml (alle Libs + Kotlin mit
  echtem Wert statt Jinja-Variable, je mit mvnrepository-URL und Maintenance-
  Constraint) und gradleInit/versions/gradle/wrapper/gradle-wrapper.properties
  (Gradle-Version; Gradle-Maintenance-Policy als Meta-Eintrag in der TOML).
- READMEs annotiert (HTML-Kommentar-Marker): versions:begin/end (generierter Block),
  vregion:begin/end (verwaltete Prosa), <!--v:KEY-->wert<!--/v--> (Einzelwert).
  Betroffen: gradleInit/README.md und kotlin-javaFX/README.md; gedriftete Werte auf
  die TOML-Wahrheit korrigiert.
- Tool (neu): tools/version_sync.py, NICHT Teil der gradleInit.py-CLI. --check
  implementiert (strikt). Test (neu): test_version_sync.py.

v0024: Fix --latest -> @* (version_policy)

- Problem: --latest setzte context['version_policy'] = '@*', aber kein Template
  referenzierte version_policy. Die Template-TOMLs trugen @pin hartcodiert.
- Loesung: in allen 6 Template-libs.versions.toml @pin -> {{ version_policy }} in den
  mvnrepository-Kommentarzeilen. Default rendert @pin (backward-compatible), --latest
  rendert @*. Test (neu): test_version_policy.py.
- Hinweis: CHECKSUMS.sha256/.sig sind nach Aenderungen neu zu signieren (sign.sh).

v0020-v0023: JDK/Kotlin Toolchain Fix, Release-Infrastruktur, CI-Fixes

1. JDK 24 Cap fuer Kotlin (v0020):
   - Problem: Kotlin 2.x unterstuetzt max JDK 24, buildSrc mit JDK 25 kompiliert -> Fehler
   - Loesung: `jvmToolchain(minOf(libs.versions.jdk.get().toInt(), 24))` in allen Templates
   - buildSrc shared Version Catalog via settings.gradle.kts
   - Precompiled script plugins nutzen VersionCatalogsExtension

2. --latest Flag (v0020):
   - `gradleInit init myApp --template kotlin-single --latest` setzt @* statt @pin
   - Template-Variable version_policy in allen libs.versions.toml

3. Release-Infrastruktur (v0021):
   - Neuer offizieller Signing Key generiert (RSA-4096)
   - OFFICIAL_PUBLIC_KEY in gradleInit.py aktualisiert
   - release.sh und sign.sh Scripts ins Repo
   - .github/workflows/release.yml Workflow

4. CI-Fixes (v0022-v0023):
   - pytest, pyyaml, cryptography zu pip Dependencies hinzugefuegt
   - Test-Context mit allen Template-Variablen erweitert (enable_clikt, company, ktor_version, etc.)
   - TestJinja2Features Tests uebersprungen (veraltete API)

## TODO

- TestJinja2Features Tests auf neue ProjectGenerator API refactoren
- Spring Boot BOM Integration
- `raw_copy` aus TEMPLATE.md verarbeiten
- Prerelease-Constraint hinzufuegen (z.B. @*-pre oder @^1.2.3-pre)
- Pseudo .git Repository fuer git-Tests in CI

## Erledigte TODOs

- [x] Tests in CI integrieren (.github/workflows/ci.yml)
- [x] OFFICIAL_PUBLIC_KEY mit echtem Key ersetzen
- [x] Verification bei Template/Module-Nutzung integrieren

## Zugehoerige Repositories

- gradleInit: https://github.com/stotz/gradleInit.git
- gradleInitTemplates: https://github.com/stotz/gradleInitTemplates.git
- gradleInitModules: https://github.com/stotz/gradleInitModules.git

## History

| Version | Aenderungen |
|---------|------------|
| v0040 | Zeilenende-unabhaengige Verifikation: _normalize_text_bytes (CRLF/CR->LF fuer Text, NUL-Binary unangetastet) in _get_file_hash, sign/verify_repository und _verify_single_file; LF-Inhalte hashen unveraendert, CRLF-committete Dateien erfordern einmaliges Neu-Signieren; Roundtrip-Test |
| v0039 | Fix CRLF der SSoT-libs.versions.toml: run_update normalisiert den Catalog nach VersionManager.update_version erneut auf LF (_write_lf); Test deckt jetzt auch den Lib-Pfad in run_update ab |
| v0038 | Fix CRLF: version_sync schreibt jetzt immer LF (_write_lf, write_bytes) - sonst broke eine CRLF-Working-Copy nach git-LF-Normalisierung die Signatur-Verifikation; Tests erweitert |
| v0037 | Fix Pre-Release bei Lib-Updates: VersionConstraintChecker.is_stable schliesst Milestone/RC/alpha/beta/SNAPSHOT aus (z.B. spring-boot 4.1.0-M4); gilt fuer versions --update und version_sync --update; Test erweitert |
| v0036 | Fix bloesses @^/@~ (SSoT): VersionConstraintChecker.anchor verankert an current, sonst fand version_sync --update keine Lib-Updates; run_update zeigt jetzt alle Status + Summary; Tests erweitert |
| v0035 | version_sync --update implementiert (Libs via Maven Central, Gradle via services.gradle.org, innerhalb Constraint; nur SSoT, --apply getrennt; 48h-Guard + --include-recent + --yes); _select_gradle_target verankert bloesses @^/@~ an current; Tests erweitert |
| v0034 | Fix Gradle-Versionsfilter: Nightly/RC/Milestone via Metadaten-Flags ausschliessen (statt String-Match); zweite Schutzschicht (nur finale X.Y.Z) in der Gradle-Zielauswahl; Tests erweitert |
| v0033 | gradleInit --update all: aktualisiert Tool + Templates + Module in einem Lauf; Helper _self_update_target (self/all/None); Test erweitert |
| v0032 | Gradle-Policy-Parser streng: nur "# gradle @<policy>" (Space vor @ Pflicht, keine =-Toleranz); Test angepasst |
| v0031 | versions --update zieht jetzt auch die Gradle-Wrapper-Version (Policy als "# gradle @..."-Kommentar in libs.versions.toml; nur distributionUrl wird umgeschrieben); Kommentar in allen 6 Templates ergaenzt; neuer Test test_gradle_update.py |
| v0030 | Fix Regression (v0029): globales --update kaperte templates/modules/versions --update; Selbst-Update nur noch ohne Subcommand; Test erweitert |
| v0029 | gradleInit --update (Selbst-Update): erkennt Git- vs Single-File-Install; git pull --ff-only bzw. signierter Download des neuesten Release-Tags mit Verifikation; neuer Test test_self_update.py |
| v0028 | Fix: gradle-wrapper.jar wurde git-ignoriert (.gitignore-Reihenfolge in 5 Templates korrigiert, Negation hinter *.jar); neuer Test test_wrapper_gitignore.py |
| v0027 | Fix JVM-Toolchain: jvmToolchain(minOf(jdk,24)) -> jvmToolchain(jdk) in allen 8 Build-Stellen (Cap obsolet seit Kotlin 2.3 JDK-25-Support); behebt JDK-25-Build; neuer Test test_toolchain.py |
| v0026 | version_sync.py --apply: schreibt SSoT-Werte in Template-TOMLs, Tool-Defaults und README-Marker; idempotent; Roundtrip-Test |
| v0025 | Versions-SSoT (versions/gradle/...) + tools/version_sync.py --check; READMEs mit Markern annotiert und auf TOML-Wahrheit korrigiert; neuer Test test_version_sync.py |
| v0024 | Fix: --latest steuert nun die Constraints (version_policy in allen Template-TOMLs statt hartcodiertem @pin); neuer Test test_version_policy.py |
| v0023 | Test-Context mit allen Template-Variablen; TestJinja2Features uebersprungen |
| v0022 | pytest/pyyaml/cryptography zu CI Dependencies |
| v0021 | OFFICIAL_PUBLIC_KEY aktualisiert (neuer Signing Key) |
| v0020 | JDK 24 Cap fuer Kotlin; --latest Flag; buildSrc shared Version Catalog |
| v0019 | dump_src.sh v2.6.0 in allen Templates |
| v0018 | Jinja2 API Migration; JDK Auto-Detection in Tests |
| v0017 | CI Fix; Maven Central auf maven-metadata.xml; test_versions.py (56 Tests); README.md komplett neu |
| v0016 | Doku-Bereinigung: GIT_FILES.md/WINDOWS_SETUP.md entfernt, 3 MDs nach docs/, README Documents-Abschnitt |
| v0015 | CI Fix: _modules_exist() resolvers/ statt dependencies/, Import-Pfade korrigiert, stdin Guard |
| v0014 | CI Security Checks (verify-signatures Job) |
| v0013 | Einheitliche LF Zeilenumbrueche (.gitattributes in allen Repos) |
| v0012 | Checksums nur fuer git-tracked Files (git ls-files) |
| v0011 | Bessere Fehlermeldung bei existierendem Key, sign.sh Script, offizieller Public Key |
| v0010 | Fix: Signatur-Verifikation auf Windows (CRLF/LF Problem) |
| v0009 | Fix: ensure_cryptography() in keys/sign/verify Commands |
| v0008 | Security Features (signing/verify), Package Management, Version Constraints, modules Command |
| v0007 | Package Management mit interaktiver Installation, --install-deps fuer CI |
| v0006 | Security: keys/sign/verify Commands, RepositorySecurity Klasse |
| v0005 | versions Command, VersionManager, npm-style Constraints, UNKNOWN Status |
| v0004 | subproject Command wiederhergestellt, SCRIPT_VERSION 1.8.0, DEFAULT_GRADLE_VERSION 9.3.1 |
| v0003 | CI Workflow Fixes, Default-Versionen, force_download_modules() |
| v0002 | .raw Suffix-Logik, .subproject Skip-Logik implementiert |
| v0001 | Initiale Version aus Upload |

---

[README.md](../README.md)

---
