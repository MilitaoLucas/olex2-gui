# dictionary.txt glossary

Agreed terms for translating `dictionary.txt`. Every entry is translated
against this list, so one English term always gets the same translation.
Draft of 2026-11-20, waiting for review. ⚑ marks the choices I am least sure
of; a native-speaking crystallographer should confirm these first.

## Rules for all languages

- **Leave these untranslated:** SHELX instructions (AFIX, HFIX, PART, FVAR,
  DFIX, DANG, SADI, SAME, SIMU, DELU, RIGU, ISOR, EADP, EXYZ, FLAT, CHIV, OMIT,
  MERG, TWIN, BASF, TREF, PATT, HKLF, CONN, BIND, FREE, SUMP, L.S., CGLS, ACTA,
  WGHT, EXTI, SWAT), program names (Olex2, ShelXL, ShelXT, olex2.refine,
  olex2.solve, SIR, Superflip, NoSpherA2), file types (CIF, HKL, INS, RES),
  symbols (Fobs, Fcalc, Uiso, Ueq, Uij, R1, wR2, GooF, Flack x, Q1), element
  symbols and space-group symbols.
- **Keep markup as it is:** HTML tags, `&nbsp;` and other entities,
  `%key%` and `$spy...` expressions, and `~...~` markers. Translate only the
  text between them.
- **Buttons:** use the form a native program would use. French, German,
  Spanish and Russian: infinitive (Affiner, Verfeinern, Refinar, Уточнить).
  Greek: a noun (Εκλέπτυνση). Japanese and Chinese: the noun or verb alone
  (精密化, 精修). Arabic: a verbal noun (تنقيح).
- **Switch states:** "On" and "Off" are states, never prepositions: Activé /
  Désactivé, An / Aus, Activado / Desactivado, Вкл. / Выкл., Ενεργό /
  Ανενεργό, オン / オフ, 开 / 关, تشغيل / إيقاف.
- **Greek:** always with accents (monotonic).
- **Japanese and Chinese:** use full-width punctuation inside sentences (、。：),
  but ASCII for symbols and numbers.
- **When unsure:** keep the English term in brackets after the translation
  (as with "restraint" below) rather than invent a word.

## Term list

The same 60 terms, in the same order, in each language.

| # | English | Note |
|---|---|---|
| 1 | refine (button) / refinement | least-squares refinement, never "filter" or "purify" |
| 2 | solve (button) / structure solution | finding the first model |
| 3 | reflection(s) | diffraction spots, never "thoughts" |
| 4 | bad reflections | outliers in the refinement |
| 5 | space group | |
| 6 | unit cell / cell | |
| 7 | asymmetric unit | |
| 8 | disorder | crystallographic disorder, never "trouble" |
| 9 | occupancy | site occupancy factor |
| 10 | ellipsoid(s) / displacement ellipsoid | |
| 11 | anisotropic / isotropic | |
| 12 | Q-peak(s) | residual density maxima |
| 13 | residual electron density | |
| 14 | difference (Fourier) map | |
| 15 | restraint | soft, weighted condition (DFIX, SIMU...) |
| 16 | constraint | exact condition (AFIX, EADP...) |
| 17 | riding model / riding atom | |
| 18 | free variable | |
| 19 | least squares | |
| 20 | standard uncertainty (s.u., esd) | |
| 21 | symmetry-equivalent | |
| 22 | grow (button) | complete fragments with symmetry equivalents |
| 23 | fragment | |
| 24 | moiety | as in "moiety formula" |
| 25 | mean plane / best line | |
| 26 | bond / bond length | |
| 27 | angle / torsion angle | |
| 28 | hydrogen atom(s) | |
| 29 | hydrogen bond | |
| 30 | structure factor | |
| 31 | resolution | |
| 32 | completeness | |
| 33 | systematic absences | |
| 34 | Laue class / point group | |
| 35 | centrosymmetric / non-centrosymmetric | |
| 36 | absolute structure / Flack parameter | |
| 37 | twin / twinning | |
| 38 | solvent mask / void | |
| 39 | direct methods / Patterson method | |
| 40 | charge flipping / dual space | |
| 41 | phase(s) | |
| 42 | weighting scheme / weight | |
| 43 | goodness of fit | |
| 44 | Wilson plot | |
| 45 | atom labels / naming (of atoms) | |
| 46 | packing | crystal packing |
| 47 | displacement parameter | |
| 48 | scattering factor | |
| 49 | anomalous dispersion | |
| 50 | Bijvoet pairs | |
| 51 | R factor | |
| 52 | tidy (button) | Olex2's automatic clean-up of the model |
| 53 | overlay / match (structures) | |
| 54 | connectivity | |
| 55 | crystal | never "quartz" |
| 56 | select / selection | |
| 57 | show / hide | |
| 58 | settings | |
| 59 | intensity / diffraction data | |
| 60 | assemble | rebuild the connectivity |

## French

| # | Term |
|---|---|
| 1 | Affiner / affinement |
| 2 | Résoudre / résolution de la structure |
| 3 | réflexion(s) |
| 4 | réflexions aberrantes |
| 5 | groupe d'espace |
| 6 | maille élémentaire / maille |
| 7 | unité asymétrique |
| 8 | désordre |
| 9 | taux d'occupation |
| 10 | ellipsoïde(s) / ellipsoïde de déplacement atomique |
| 11 | anisotrope / isotrope |
| 12 | pic(s) Q |
| 13 | densité électronique résiduelle |
| 14 | carte de Fourier différence |
| 15 | ⚑ restreinte (contrainte souple) |
| 16 | contrainte |
| 17 | ⚑ modèle riding / atome porté |
| 18 | variable libre |
| 19 | moindres carrés |
| 20 | incertitude-type (s.u.) |
| 21 | équivalent par symétrie |
| 22 | Compléter |
| 23 | fragment |
| 24 | entité |
| 25 | plan moyen / droite moyenne |
| 26 | liaison / longueur de liaison |
| 27 | angle / angle de torsion |
| 28 | atome(s) d'hydrogène |
| 29 | liaison hydrogène |
| 30 | facteur de structure |
| 31 | résolution |
| 32 | complétude |
| 33 | extinctions systématiques |
| 34 | classe de Laue / groupe ponctuel |
| 35 | centrosymétrique / non centrosymétrique |
| 36 | structure absolue / paramètre de Flack |
| 37 | macle / maclage |
| 38 | masque de solvant / cavité |
| 39 | méthodes directes / méthode de Patterson |
| 40 | inversion de charge (charge flipping) / espace dual |
| 41 | phase(s) |
| 42 | schéma de pondération / poids |
| 43 | qualité de l'ajustement (GooF) |
| 44 | diagramme de Wilson |
| 45 | étiquettes des atomes / nommage des atomes |
| 46 | empilement |
| 47 | paramètre de déplacement atomique |
| 48 | facteur de diffusion |
| 49 | dispersion anomale |
| 50 | paires de Bijvoet |
| 51 | facteur R |
| 52 | Nettoyer |
| 53 | Superposer / Faire correspondre |
| 54 | connectivité |
| 55 | cristal |
| 56 | Sélectionner / sélection |
| 57 | Afficher / Masquer |
| 58 | Paramètres |
| 59 | intensité / données de diffraction |
| 60 | Assembler |

Note: French uses "extinctions systématiques" for absences, so the
extinction correction (EXTI) is "correction d'extinction secondaire" to keep
the two apart.

## German

The existing German column already uses most of these; mainly for consistency.

| # | Term |
|---|---|
| 1 | Verfeinern / Verfeinerung |
| 2 | Lösen / Strukturlösung |
| 3 | Reflex(e) |
| 4 | Schlechte Reflexe (Ausreißer) |
| 5 | Raumgruppe |
| 6 | Elementarzelle / Zelle |
| 7 | asymmetrische Einheit |
| 8 | Fehlordnung |
| 9 | Besetzung (Besetzungsfaktor) |
| 10 | Ellipsoide / Auslenkungsellipsoid |
| 11 | anisotrop / isotrop |
| 12 | Q-Peak(s) |
| 13 | Restelektronendichte |
| 14 | Differenz-Fourier-Karte |
| 15 | Restraint |
| 16 | Constraint |
| 17 | Reitermodell / Reiteratom |
| 18 | freie Variable |
| 19 | kleinste Fehlerquadrate |
| 20 | Standardunsicherheit (s.u.) |
| 21 | symmetrieäquivalent |
| 22 | Vervollständigen |
| 23 | Fragment |
| 24 | Baueinheit (moiety) |
| 25 | beste Ebene / beste Gerade |
| 26 | Bindung / Bindungslänge |
| 27 | Winkel / Torsionswinkel |
| 28 | Wasserstoffatom(e) |
| 29 | Wasserstoffbrücke |
| 30 | Strukturfaktor |
| 31 | Auflösung |
| 32 | Vollständigkeit |
| 33 | systematische Auslöschungen |
| 34 | Laue-Klasse / Punktgruppe |
| 35 | zentrosymmetrisch / nicht zentrosymmetrisch |
| 36 | absolute Struktur / Flack-Parameter |
| 37 | Zwilling / Verzwillingung |
| 38 | Lösungsmittelmaske / Hohlraum |
| 39 | Direkte Methoden / Patterson-Methode |
| 40 | Charge-Flipping / Dual-Space |
| 41 | Phase(n) |
| 42 | Wichtungsschema / Wichtung |
| 43 | Goodness of Fit (GooF) |
| 44 | Wilson-Plot |
| 45 | Atomnamen / Benennung der Atome |
| 46 | Packung |
| 47 | Auslenkungsparameter |
| 48 | Atomformfaktor |
| 49 | anomale Dispersion |
| 50 | Bijvoet-Paare |
| 51 | R-Wert |
| 52 | Aufräumen |
| 53 | Überlagern / Strukturerkennung |
| 54 | Konnektivität |
| 55 | Kristall |
| 56 | ⚑ Auswählen / Auswahl |
| 57 | Anzeigen / Ausblenden |
| 58 | Einstellungen |
| 59 | Intensität / Beugungsdaten |
| 60 | Zusammenfügen |

Notes: German crystallographers say "Restraint" and "Constraint", so those
stay. ⚑ The current column mixes "Selektion/Selektieren" and "Anwählen";
pick one. I suggest "Auswahl/Auswählen".

Agreed 2026-11-20: "Tools" stays "Tools", never "Werkzeuge" (also in compounds:
Chemie-Tools, Symmetrie-Tools, Toolbox, Haupt-Toolbar, Tool-Bereich).

## Spanish

| # | Term |
|---|---|
| 1 | Refinar / refinamiento |
| 2 | Resolver / resolución de la estructura |
| 3 | reflexión(es) |
| 4 | reflexiones anómalas |
| 5 | grupo espacial |
| 6 | celda unidad / celda |
| 7 | unidad asimétrica |
| 8 | desorden |
| 9 | ocupación |
| 10 | elipsoide(s) / elipsoide de desplazamiento |
| 11 | anisótropo / isótropo |
| 12 | pico(s) Q |
| 13 | densidad electrónica residual |
| 14 | mapa de Fourier diferencia |
| 15 | ⚑ restricción (restraint) |
| 16 | ⚑ ligadura (constraint) |
| 17 | ⚑ modelo riding (átomos dependientes) |
| 18 | variable libre |
| 19 | mínimos cuadrados |
| 20 | incertidumbre estándar (s.u.) |
| 21 | equivalente por simetría |
| 22 | Completar |
| 23 | fragmento |
| 24 | entidad |
| 25 | plano medio / mejor recta |
| 26 | enlace / distancia de enlace |
| 27 | ángulo / ángulo de torsión |
| 28 | átomo(s) de hidrógeno |
| 29 | enlace de hidrógeno |
| 30 | factor de estructura |
| 31 | resolución |
| 32 | completitud |
| 33 | ausencias sistemáticas |
| 34 | clase de Laue / grupo puntual |
| 35 | centrosimétrico / no centrosimétrico |
| 36 | estructura absoluta / parámetro de Flack |
| 37 | macla / maclado |
| 38 | máscara de disolvente / hueco |
| 39 | métodos directos / método de Patterson |
| 40 | inversión de carga (charge flipping) / espacio dual |
| 41 | fase(s) |
| 42 | esquema de pesos / peso |
| 43 | bondad del ajuste (GooF) |
| 44 | gráfico de Wilson |
| 45 | etiquetas de los átomos / nombrado de átomos |
| 46 | empaquetamiento |
| 47 | parámetro de desplazamiento |
| 48 | factor de dispersión atómico |
| 49 | dispersión anómala |
| 50 | pares de Bijvoet |
| 51 | factor R |
| 52 | Ordenar |
| 53 | Superponer / Emparejar |
| 54 | conectividad |
| 55 | cristal |
| 56 | Seleccionar / selección |
| 57 | Mostrar / Ocultar |
| 58 | Configuración |
| 59 | intensidad / datos de difracción |
| 60 | Ensamblar |

Note: "refinamiento" rather than "afinamiento", as it is the word most
Spanish-speaking crystallographers use.

## Russian

| # | Term |
|---|---|
| 1 | Уточнить / уточнение |
| 2 | Решить / решение структуры |
| 3 | отражение (отражения) |
| 4 | плохие отражения (выбросы) |
| 5 | пространственная группа |
| 6 | элементарная ячейка / ячейка |
| 7 | независимая часть ячейки |
| 8 | разупорядочение |
| 9 | заселённость |
| 10 | эллипсоиды / эллипсоид атомных смещений |
| 11 | анизотропный / изотропный |
| 12 | Q-пик(и) |
| 13 | остаточная электронная плотность |
| 14 | разностный синтез Фурье |
| 15 | мягкое ограничение (restraint) |
| 16 | жёсткое ограничение (constraint) |
| 17 | модель «наездника» |
| 18 | свободная переменная |
| 19 | метод наименьших квадратов (МНК) |
| 20 | стандартная неопределённость (s.u.) |
| 21 | симметрически эквивалентный |
| 22 | Достроить |
| 23 | фрагмент |
| 24 | структурная единица |
| 25 | средняя плоскость / наилучшая прямая |
| 26 | связь / длина связи |
| 27 | валентный угол / торсионный угол |
| 28 | атом(ы) водорода |
| 29 | водородная связь |
| 30 | структурный фактор |
| 31 | разрешение |
| 32 | полнота |
| 33 | систематические погасания |
| 34 | класс Лауэ / точечная группа |
| 35 | центросимметричный / нецентросимметричный |
| 36 | абсолютная структура / параметр Флэка |
| 37 | двойник / двойникование |
| 38 | маска растворителя / полость |
| 39 | прямые методы / метод Паттерсона |
| 40 | ⚑ переворот заряда (charge flipping) / двойственное пространство (dual space) |
| 41 | фаза (фазы) |
| 42 | весовая схема / вес |
| 43 | критерий согласия (GooF) |
| 44 | график Вильсона |
| 45 | метки атомов / именование атомов |
| 46 | упаковка |
| 47 | параметр атомного смещения |
| 48 | атомный фактор рассеяния |
| 49 | аномальное рассеяние |
| 50 | ⚑ пары Бейвута |
| 51 | R-фактор |
| 52 | Привести в порядок |
| 53 | Наложить / Сопоставить |
| 54 | связность |
| 55 | кристалл |
| 56 | Выделить / выделение |
| 57 | Показать / Скрыть |
| 58 | Настройки |
| 59 | интенсивность / дифракционные данные |
| 60 | Собрать |

Note: "связь" is the bond, so a constraint is "жёсткое ограничение", never
"связь".

## Greek

| # | Term |
|---|---|
| 1 | Εκλέπτυνση / εκλέπτυνση |
| 2 | Επίλυση / επίλυση της δομής |
| 3 | ανάκλαση (ανακλάσεις) |
| 4 | προβληματικές ανακλάσεις |
| 5 | ομάδα χώρου |
| 6 | στοιχειώδης κυψελίδα / κυψελίδα |
| 7 | ασύμμετρη μονάδα |
| 8 | αταξία |
| 9 | κατάληψη (συντελεστής κατάληψης) |
| 10 | ελλειψοειδή / ελλειψοειδές μετατόπισης |
| 11 | ανισότροπος / ισότροπος |
| 12 | κορυφή (κορυφές) Q |
| 13 | υπολειμματική ηλεκτρονική πυκνότητα |
| 14 | χάρτης διαφοράς Fourier |
| 15 | ⚑ ήπιος περιορισμός (restraint) |
| 16 | ⚑ αυστηρός περιορισμός (constraint) |
| 17 | ⚑ μοντέλο riding (εξαρτημένα άτομα) |
| 18 | ελεύθερη μεταβλητή |
| 19 | ελάχιστα τετράγωνα |
| 20 | τυπική αβεβαιότητα (s.u.) |
| 21 | ισοδύναμο λόγω συμμετρίας |
| 22 | Συμπλήρωση |
| 23 | τμήμα |
| 24 | δομική μονάδα |
| 25 | μέσο επίπεδο / βέλτιστη ευθεία |
| 26 | δεσμός / μήκος δεσμού |
| 27 | γωνία / γωνία στρέψης |
| 28 | άτομο (άτομα) υδρογόνου |
| 29 | δεσμός υδρογόνου |
| 30 | παράγοντας δομής |
| 31 | διακριτική ικανότητα |
| 32 | πληρότητα |
| 33 | συστηματικές απουσίες |
| 34 | κλάση Laue / σημειακή ομάδα |
| 35 | κεντροσυμμετρικός / μη κεντροσυμμετρικός |
| 36 | απόλυτη δομή / παράμετρος Flack |
| 37 | δίδυμο / διδυμία |
| 38 | μάσκα διαλύτη / κοιλότητα |
| 39 | άμεσες μέθοδοι / μέθοδος Patterson |
| 40 | αναστροφή φορτίου (charge flipping) / δυϊκός χώρος |
| 41 | φάση (φάσεις) |
| 42 | σχήμα στάθμισης / βάρος |
| 43 | δείκτης καλής προσαρμογής (GooF) |
| 44 | διάγραμμα Wilson |
| 45 | ετικέτες ατόμων / ονοματοδοσία ατόμων |
| 46 | ⚑ κρυσταλλική στοίβαξη |
| 47 | παράμετρος μετατόπισης |
| 48 | παράγοντας σκέδασης |
| 49 | ανώμαλη διασπορά |
| 50 | ζεύγη Bijvoet |
| 51 | συντελεστής R |
| 52 | Τακτοποίηση |
| 53 | Υπέρθεση / Αντιστοίχιση |
| 54 | συνδεσιμότητα |
| 55 | κρύσταλλος |
| 56 | Επιλογή |
| 57 | Εμφάνιση / Απόκρυψη |
| 58 | Ρυθμίσεις |
| 59 | ένταση / δεδομένα περίθλασης |
| 60 | Συναρμολόγηση |

## Japanese

| # | Term |
|---|---|
| 1 | 精密化 |
| 2 | 構造決定 |
| 3 | 反射 |
| 4 | 不良反射 |
| 5 | 空間群 |
| 6 | 単位格子 / 格子 |
| 7 | 非対称単位 |
| 8 | ディスオーダー |
| 9 | 占有率 |
| 10 | 楕円体 / 原子変位楕円体 |
| 11 | 異方性 / 等方性 |
| 12 | Qピーク |
| 13 | 残差電子密度 |
| 14 | 差フーリエ図 |
| 15 | ⚑ 束縛（リストレイント） |
| 16 | ⚑ 拘束（コンストレイント） |
| 17 | ライディングモデル |
| 18 | 自由変数 |
| 19 | 最小二乗法 |
| 20 | 標準不確かさ (s.u.) |
| 21 | 対称等価 |
| 22 | ⚑ 対称展開 |
| 23 | フラグメント |
| 24 | 構成単位 |
| 25 | 平均平面 / 最適直線 |
| 26 | 結合 / 結合距離 |
| 27 | 結合角 / ねじれ角 |
| 28 | 水素原子 |
| 29 | 水素結合 |
| 30 | 構造因子 |
| 31 | 分解能 |
| 32 | 完全性 |
| 33 | 消滅則 |
| 34 | ラウエ群 / 点群 |
| 35 | 中心対称 / 非中心対称 |
| 36 | 絶対構造 / Flackパラメーター |
| 37 | 双晶 |
| 38 | 溶媒マスク / 空隙 |
| 39 | 直接法 / パターソン法 |
| 40 | チャージフリッピング法 / デュアルスペース法 |
| 41 | 位相 |
| 42 | 重み付けスキーム / 重み |
| 43 | 適合度 (GooF) |
| 44 | ウィルソンプロット |
| 45 | 原子ラベル / 原子の命名 |
| 46 | パッキング |
| 47 | 原子変位パラメーター |
| 48 | 原子散乱因子 |
| 49 | 異常分散 |
| 50 | Bijvoet対 |
| 51 | R因子 |
| 52 | 整理 |
| 53 | 重ね合わせ / マッチング |
| 54 | 結合関係 |
| 55 | 結晶 |
| 56 | 選択 |
| 57 | 表示 / 非表示 |
| 58 | 設定 |
| 59 | 強度 / 回折データ |
| 60 | 再構築 |

Note: ⚑ Japanese usage of 拘束 and 束縛 for constraint and restraint is not
uniform; the katakana in brackets keeps the meaning clear either way.

## Chinese (simplified)

The existing column is mostly good; these keep it consistent.

| # | Term |
|---|---|
| 1 | 精修 |
| 2 | 解析 / 结构解析 |
| 3 | 衍射点 |
| 4 | 异常衍射点 |
| 5 | 空间群 |
| 6 | 晶胞 |
| 7 | 不对称单元 |
| 8 | 无序 |
| 9 | 占有率 |
| 10 | 椭球 / 位移椭球 |
| 11 | 各向异性 / 各向同性 |
| 12 | Q峰 |
| 13 | 残余电子密度 |
| 14 | 差值傅里叶图 |
| 15 | 限制 |
| 16 | 约束 |
| 17 | 骑式模型 |
| 18 | 自由变量 |
| 19 | 最小二乘 |
| 20 | 标准不确定度 (s.u.) |
| 21 | 对称等效 |
| 22 | 生长 |
| 23 | 片段 |
| 24 | 结构单元 |
| 25 | 平均平面 / 最佳直线 |
| 26 | 键 / 键长 |
| 27 | 键角 / 扭转角 |
| 28 | 氢原子 |
| 29 | 氢键 |
| 30 | 结构因子 |
| 31 | 分辨率 |
| 32 | 完整度 |
| 33 | 系统消光 |
| 34 | 劳厄群 / 点群 |
| 35 | 中心对称 / 非中心对称 |
| 36 | 绝对结构 / Flack参数 |
| 37 | 孪晶 |
| 38 | 溶剂掩模 / 空穴 |
| 39 | 直接法 / 帕特森法 |
| 40 | 电荷翻转法 / 双空间法 |
| 41 | 相位 |
| 42 | 权重方案 / 权重 |
| 43 | 拟合优度 (GooF) |
| 44 | Wilson图 |
| 45 | 原子标签 / 原子命名 |
| 46 | 堆积 |
| 47 | 位移参数 |
| 48 | 原子散射因子 |
| 49 | 反常色散 |
| 50 | Bijvoet对 |
| 51 | R因子 |
| 52 | 整理 |
| 53 | 叠合 / 匹配 |
| 54 | 连接关系 |
| 55 | 晶体 |
| 56 | 选择 |
| 57 | 显示 / 隐藏 |
| 58 | 设置 |
| 59 | 强度 / 衍射数据 |
| 60 | 组装 |

Note: "Overlay" is currently 覆盖 ("cover"); 叠合 is the crystallographic
word for superimposing structures.

## Arabic

| # | Term |
|---|---|
| 1 | تنقيح / تنقيح البنية |
| 2 | حلّ / حلّ البنية |
| 3 | انعكاس (انعكاسات) |
| 4 | انعكاسات شاذة |
| 5 | زمرة فراغية |
| 6 | خلية الوحدة / خلية |
| 7 | الوحدة اللاتماثلية |
| 8 | عدم الانتظام |
| 9 | نسبة الإشغال |
| 10 | مجسمات ناقصية / مجسم ناقصي للإزاحة |
| 11 | متباين الخواص / متماثل الخواص |
| 12 | قمم Q |
| 13 | الكثافة الإلكترونية المتبقية |
| 14 | خريطة فورييه الفرقية |
| 15 | قيد مرن (restraint) |
| 16 | قيد صارم (constraint) |
| 17 | ⚑ نموذج الامتطاء (riding) |
| 18 | متغير حر |
| 19 | المربعات الصغرى |
| 20 | الارتياب المعياري (s.u.) |
| 21 | مكافئ تناظرياً |
| 22 | إكمال |
| 23 | جزء |
| 24 | وحدة بنائية |
| 25 | المستوى المتوسط / أفضل خط |
| 26 | رابطة / طول الرابطة |
| 27 | زاوية / زاوية الالتواء |
| 28 | ذرات الهيدروجين |
| 29 | رابطة هيدروجينية |
| 30 | عامل البنية |
| 31 | الدقة (قدرة التمييز) |
| 32 | الاكتمال |
| 33 | الغيابات المنتظمة |
| 34 | صنف لاوي / زمرة نقطية |
| 35 | متمركز التناظر / غير متمركز التناظر |
| 36 | البنية المطلقة / معامل فلاك |
| 37 | توأم بلوري / التوأمة |
| 38 | قناع المذيب / فجوة |
| 39 | الطرق المباشرة / طريقة باترسون |
| 40 | قلب الشحنة (charge flipping) / الفضاء المزدوج |
| 41 | طور (أطوار) |
| 42 | مخطط الترجيح / وزن |
| 43 | جودة التوافق (GooF) |
| 44 | مخطط ويلسون |
| 45 | تسميات الذرات / تسمية الذرات |
| 46 | التراص البلوري |
| 47 | معامل الإزاحة |
| 48 | عامل التشتت الذري |
| 49 | التشتت الشاذ |
| 50 | أزواج بايفوت |
| 51 | عامل R |
| 52 | ترتيب |
| 53 | تراكب / مطابقة |
| 54 | الترابط |
| 55 | بلورة |
| 56 | تحديد |
| 57 | إظهار / إخفاء |
| 58 | الإعدادات |
| 59 | الشدة / بيانات الحيود |
| 60 | تجميع |

Note: Olex2 can't yet lay out right-to-left text or join Arabic letters, in
either wxHTML or the PIL-drawn buttons. Correct Arabic will still look broken
on screen until that is fixed.
