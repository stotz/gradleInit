# TODO

[README.md](../README.md)  

[SECURITY.md](SECURITY.md)  
[REPOSITORIES.md](REPOSITORIES.md)

---

[![TODO](https://img.shields.io/badge/TODO-blue.svg)](TODO)




## Aktueller Stand (v0042)

gradleInit ist ein Python-basiertes Tool zur Generierung von Kotlin/Gradle-Projekten aus Templates.
Verwendet Jinja2 fuer Template-Verarbeitung mit inline Hint-System.
SCRIPT_VERSION (semantisch, Git-Repo) ist aktuell 1.12.0; die 4-stellige AI-Versionierung
ist davon getrennt und laeuft linear (zuletzt v0042).

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
