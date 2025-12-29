"""
Configuration settings for the Italian Parliament Speech Analysis.

All configurable parameters are centralized here.
"""

# =============================================================================
# DATA FETCHING
# =============================================================================

# Maximum number of speeches to fetch
FETCH_LIMIT = 50000

# Number of sessions to scrape per source
SESSIONS_TO_FETCH = 500

# Data source: 'senate', 'camera', or 'both'
DATA_SOURCE = 'both'

# How many months back to look for camera.it sessions
MONTHS_BACK = 12

# Legislature number (19 = XIX Legislature, 2022-present)
LEGISLATURE = 19

# Minimum word count for a speech to be included
MIN_WORDS = 30

# Maximum age (in days) for cached data before automatic refresh
CACHE_MAX_AGE_DAYS = 7

# Party name normalization - maps various spellings to canonical names
# This unifies party names between Camera and Senato
PARTY_NORMALIZATION = {
    # Forza Italia
    'FI-BP-PPE': 'Forza Italia',
    'FI-PPE': 'Forza Italia',
    'FORZA ITALIA': 'Forza Italia',
    
    # Fratelli d'Italia
    'FdI': "Fratelli d'Italia",
    'FDI': "Fratelli d'Italia",
    'FDI-AN': "Fratelli d'Italia",
    
    # Lega
    'LEGA': 'Lega',
    "LSP-PSd'Az": 'Lega',
    'LSP': 'Lega',
    
    # Partito Democratico
    'PD-IDP': 'PD',
    'PD': 'PD',
    
    # Movimento 5 Stelle
    'M5S': 'M5S',
    
    # Italia Viva / Centro
    'IV-C-RE': 'Italia Viva',
    'IV': 'Italia Viva',
    
    # Azione / Renew Europe
    'AZ-PER-RE': 'Azione-RE',
    'Misto-Az-RE': 'Azione-RE',
    'AZIONE-PER': 'Azione-RE',
    
    # AVS (Alleanza Verdi Sinistra)
    'AVS': 'AVS',
    'Misto-AVS': 'AVS',
    
    # Noi Moderati
    'NM(N-C-U-I': 'Noi Moderati',
    'NM(N-C-U-I)': 'Noi Moderati',
    'NM': 'Noi Moderati',
    
    # Gruppo Misto
    'MISTO': 'Misto',
    'Misto': 'Misto',
    'MISTO-+EUROPA': 'Misto-PiùEuropa',
    'MISTO-MIN.LING.': 'Misto-MinoranzeLing',
}


# =============================================================================
# POLITICAL COALITIONS (for left/right polarization analysis)
# =============================================================================

# Right-wing coalition (Governo Meloni)
RIGHT_PARTIES = {
    "Fratelli d'Italia", "FdI", "FDI",
    "Lega", "LEGA",
    "Forza Italia", "FI", "FI-PPE", "FI-BP-PPE",
    "Noi Moderati", "NM", "NM(N-C-U-I)", "NM(N-C-U-I",
}

# Left-wing / Opposition parties
LEFT_PARTIES = {
    "Partito Democratico", "PD", "PD-IDP",
    "Movimento 5 Stelle", "M5S",
    "AVS", "Alleanza Verdi Sinistra", "Misto-AVS",
    "+Europa", "Misto-PiùEuropa", "MISTO-+EUROPA",
}

# Center parties (often swing/third pole)
CENTER_PARTIES = {
    "Azione", "Azione-RE", "Azione-IV-RE", "IV-C-RE",
    "Italia Viva", "IV",
    "Misto", "MISTO",
}


# =============================================================================
# ANALYSIS
# =============================================================================

# Number of semantic clusters for K-Means (used if TOPIC_CLUSTERS is None)
N_CLUSTERS = 8

# Custom topic clusters with keywords (set to None to use K-Means auto-clustering)
# Format: { cluster_id: { 'label': 'Topic Name', 'keywords': ['keyword1', 'keyword2', ...] } }
# Speeches are assigned to the topic with most keyword matches
TOPIC_CLUSTERS = {
    0: {
        'label': 'Fisco e Finanza Pubblica',
        'keywords': [
            'bilancio', 'manovra', 'def', 'pil', 'debito pubblico', 'spread', 
            'inflazione', 'tasse', 'fisco', 'iva', 'irpef', 'flat tax', 'evasione fiscale', 
            'cuneo fiscale', 'investimenti', 'pnrr', 'mef', 'bce', 'finanziaria', 'gettito'
        ]
    },
    1: {
        'label': 'Lavoro e Imprese',
        'keywords': [
            'lavoro', 'occupazione', 'disoccupazione', 'imprese', 'pmi', 'industria', 
            'made in italy', 'export', 'stipendi', 'salari', 'pensioni', 'precariato', 
            'contratti', 'sindacati', 'sciopero', 'bonus', 'reddito di cittadinanza', 'sussidi',
            'sicurezza sul lavoro', 'inail', 'cig'
        ]
    },
    2: {
        'label': 'Sanità',
        'keywords': [
            'sanità', 'salute', 'ssn', 'servizio sanitario', 'ospedali', 'medici', 'infermieri', 
            'pronto soccorso', 'liste d\'attesa', 'ticket', 'farmaci', 'vaccini', 'prevenzione', 
            'pandemia', 'emergenza sanitaria', 'ricerca medica', 'asl'
        ]
    },
    3: {
        'label': 'Welfare e Famiglia',
        'keywords': [
            'welfare', 'sociale', 'assistenza', 'disabilità', 'fragilità', 'anziani', 
            'non autosufficienza', 'caregiver', 'famiglia', 'natalità', 'assegno unico', 
            'asili nido', 'terzo settore', 'volontariato', 'inclusione sociale', 'povertà'
        ]
    },
    4: {
        'label': 'Ambiente e Energia',
        'keywords': [
            'energia', 'gas', 'petrolio', 'bollette', 'rinnovabili', 'fotovoltaico', 
            'eolico', 'nucleare', 'transizione ecologica', 'efficientamento', 
            'ambiente', 'clima', 'cambiamento climatico', 'emissioni', 'sostenibilità', 
            'rifiuti', 'termovalorizzatore', 'differenziata', 'siccità', 'dissesto idrogeologico'
        ]
    },
    5: {
        'label': 'Giustizia e Legalità',
        'keywords': [
            'giustizia', 'magistratura', 'processo', 'penale', 'civile', 'tribunali', 
            'carceri', 'detenuti', '41 bis', 'mafia', 'criminalità', 'legalità', 
            'antimafia', 'codice penale', 'riforma giustizia', 'prescrizione', 'intercettazioni',
            'nordio', 'cartabia'
        ]
    },
    6: {
        'label': 'Immigrazione',
        'keywords': [
            'immigrazione', 'migranti', 'sbarchi', 'lampedusa', 'rotta balcanica', 'mediterraneo', 
            'ong', 'scafisti', 'trafficanti', 'teatro', 'frontiere', 'confini', 'accoglienza', 
            'cpr', 'rimpatri', 'espulsioni', 'asilo', 'rifugiati', 'clandestini'
        ]
    },
    7: {
        'label': 'Diritti Civili',
        'keywords': [
            'diritti civili', 'libertà', 'discriminazione', 'razzismo', 'violenza sulle donne', 
            'femminicidio', 'pari opportunità', 'lgbt', 'unioni civili', 'famiglie arcobaleno', 
            'omotransfobia', 'fine vita', 'eutanasia', 'suicidio assistito', 'aborto', '194', 
            'ius scholae', 'cittadinanza'
        ]
    },
    8: {
        'label': 'Scuola e Università',
        'keywords': [
            'scuola', 'istruzione', 'università', 'atenei', 'formazione', 'didattica', 
            'studenti', 'alunni', 'docenti', 'professori', 'cattedre', 'precari scuola', 'concorsi', 
            'merito', 'abbandono scolastico', 'edilizia scolastica', 'erasmus', 'ricerca', 'laurea'
        ]
    },
    9: {
        'label': 'Agricoltura',
        'keywords': [
            'agricoltura', 'agricoltori', 'trattori', 'coltivatori', 'pac', 'allevatori', 'pesca',
            'filiera', 'alimentare', 'grano', 'vino', 'siccità', 'peste suina', 'fauna selvatica'
        ]
    },
    10: {
        'label': 'Politica Estera e Difesa',
        'keywords': [
            'esteri', 'diplomazia', 'internazionale', 'geopolitica', 'ucraina', 'russia', 'putin', 
            'zelensky', 'medio oriente', 'gaza', 'israele', 'hamas', 'palestina', 'onu', 'nato', 
            'alleanza atlantica', 'difesa', 'esercito', 'forze armate', 'armi', 'spese militari', 'pace'
        ]
    },
    11: {
        'label': 'Infrastrutture e Trasporti',
        'keywords': [
            'infrastrutture', 'opere pubbliche', 'cantieri', 'codice appalti', 'ponte sullo stretto', 
            'trasporti', 'mobilità', 'ferrovie', 'treni', 'alta velocità', 'tav', 'strade', 
            'autostrade', 'porti', 'aeroporti', 'trasporto pubblico locale'
        ]
    },
    12: {
        'label': 'Riforme Istituzionali',
        'keywords': [
            'premierato', 'autonomia differenziata', 'regionalismo', 'riforma costituzionale', 
            'elezione diretta', 'legge elettorale', 'bicameralismo', 'regioni', 'province', 
            'semplificazione amministrativa', 'burocrazia'
        ]
    }
}

# Set to None to use automatic K-Means clustering instead:
# TOPIC_CLUSTERS = None

# Embedding model (multilingual)
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# Dimensionality reduction method: 'pca' or 'tsne'
REDUCTION_METHOD = "pca"

# t-SNE perplexity (only used if REDUCTION_METHOD = 'tsne')
TSNE_PERPLEXITY = 30


# =============================================================================
# STOPWORDS - Expanded comprehensive Italian stopwords
# =============================================================================

STOP_WORDS = {
    # === ARTICLES & PREPOSITIONS ===
    'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una',
    'di', 'a', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra',
    'del', 'della', 'dei', 'degli', 'delle', 
    'al', 'alla', 'ai', 'agli', 'alle',
    'dal', 'dalla', 'dai', 'dagli', 'dalle', 
    'nel', 'nella', 'nei', 'negli', 'nelle',
    'sul', 'sulla', 'sui', 'sugli', 'sulle',
    'col', 'coi', 'pel', 'pei',
    # Truncated forms commonly found after tokenization (e.g. "dell'Italia" -> "dell")
    'dell', 'dall', 'nell', 'sull', 'all', 'gl', 'un', 'c', 'l', 'd', 'v', 'n', 's',
    
    # === PRONOUNS ===
    'io', 'tu', 'egli', 'ella', 'esso', 'essa', 'noi', 'voi', 'essi', 'esse',
    'lui', 'lei', 'loro', 'me', 'te', 'sé',
    'mi', 'ti', 'si', 'ci', 'vi', 'ne', 'lo', 'la', 'li', 'le',
    'mio', 'mia', 'miei', 'mie', 'tuo', 'tua', 'tuoi', 'tue',
    'suo', 'sua', 'suoi', 'sue', 'nostro', 'nostra', 'nostri', 'nostre',
    'vostro', 'vostra', 'vostri', 'vostre',
    'questo', 'questa', 'questi', 'queste', 'quello', 'quella', 'quelli', 'quelle',
    'ciò', 'costui', 'costei', 'costoro', 'colui', 'colei', 'coloro',
    'chi', 'che', 'cui', 'quale', 'quali',
    
    # === INTERROGATIVES ===
    'cosa', 'come', 'dove', 'quando', 'perché', 'quanto', 'quanta', 'quanti', 'quante',
    
    # === INDEFINITES ===
    'ogni', 'tutto', 'tutti', 'tutta', 'tutte', 
    'altro', 'altri', 'altra', 'altre', 'altrui',
    'stesso', 'stessa', 'stessi', 'stesse',
    'proprio', 'propria', 'propri', 'proprie',
    'qualche', 'qualcuno', 'qualcuna', 'qualcosa', 
    'chiunque', 'checché', 'chicchessia',
    'nessuno', 'nessuna', 'niente', 'nulla',
    'alcuno', 'alcuna', 'alcuni', 'alcune',
    'ciascuno', 'ciascuna', 'tale', 'tali',
    'certo', 'certa', 'certi', 'certe',
    'vario', 'varia', 'vari', 'varie',
    'troppo', 'troppa', 'troppi', 'troppe',
    'poco', 'poca', 'pochi', 'poche',
    'molto', 'molta', 'molti', 'molte',
    'tanto', 'tanta', 'tanti', 'tante',
    'parecchio', 'parecchia', 'parecchi', 'parecchie',
    
    # === VERBS: ESSERE ===
    'essere', 'sono', 'sei', 'è', 'siamo', 'siete',
    'ero', 'eri', 'era', 'eravamo', 'eravate', 'erano',
    'fui', 'fosti', 'fu', 'fummo', 'foste', 'furono',
    'sarò', 'sarai', 'sarà', 'saremo', 'sarete', 'saranno',
    'sia', 'siate', 'siano', 'fossi', 'fosse', 'fossimo', 'fossero',
    'sarei', 'saresti', 'sarebbe', 'saremmo', 'sareste', 'sarebbero',
    'stato', 'stata', 'stati', 'state', 'essendo',
    
    # === VERBS: AVERE ===
    'avere', 'ho', 'hai', 'ha', 'abbiamo', 'avete', 'hanno',
    'avevo', 'avevi', 'aveva', 'avevamo', 'avevate', 'avevano',
    'ebbi', 'avesti', 'ebbe', 'avemmo', 'aveste', 'ebbero',
    'avrò', 'avrai', 'avrà', 'avremo', 'avrete', 'avranno',
    'abbia', 'abbiate', 'abbiano', 'avessi', 'avesse', 'avessimo', 'avessero',
    'avrei', 'avresti', 'avrebbe', 'avremmo', 'avreste', 'avrebbero',
    'avuto', 'avuta', 'avuti', 'avute', 'avendo',
    
    # === COMMON VERBS ===
    'fare', 'fatto', 'fatta', 'fatti', 'fatte', 'fa', 'fanno', 'facendo', 'farà',
    'dire', 'detto', 'detta', 'detti', 'dette', 'dice', 'dicendo', 'dirà',
    'andare', 'andato', 'va', 'vanno', 'andando', 'andrà',
    'venire', 'venuto', 'viene', 'vengono', 'venendo', 'verrà',
    'potere', 'può', 'possono', 'potuto', 'potrà', 'potrebbe',
    'volere', 'vuole', 'vogliono', 'voluto', 'vorrà', 'vorrebbe',
    'dovere', 'deve', 'devono', 'dovuto', 'dovrà', 'dovrebbe',
    'stare', 'sta', 'stanno', 'stando', 'starà',
    'dare', 'dà', 'danno', 'dato', 'data', 'dati', 'date',
    'sapere', 'sa', 'sanno', 'saputo', 'saprà',
    'vedere', 'vede', 'vedono', 'visto', 'vista', 'vedrà',
    'prendere', 'prende', 'preso', 'presa', 'prenderà',
    'mettere', 'mette', 'messo', 'messa', 'metterà',
    'trovare', 'trova', 'trovato', 'troverà',
    'sentire', 'sente', 'sentito', 'sentirà',
    'parlare', 'parla', 'parlato', 'parlerà',
    'pensare', 'pensa', 'pensato', 'penserà',
    'credere', 'crede', 'creduto', 'crederà',
    'chiamare', 'chiama', 'chiamato', 'chiamerà',
    'portare', 'porta', 'portato', 'porterà',
    'passare', 'passa', 'passato', 'passerà',
    'restare', 'resta', 'restato', 'resterà',
    'lasciare', 'lascia', 'lasciato', 'lascerà',
    'tenere', 'tiene', 'tenuto', 'terrà',
    'seguire', 'segue', 'seguito', 'seguirà',
    'rendere', 'rende', 'reso', 'renderà',
    
    # === ADVERBS ===
    'non', 'più', 'già', 'ancora', 'sempre', 'mai', 'ora', 'adesso', 
    'oggi', 'ieri', 'domani', 'qui', 'qua', 'là', 'lì',
    'molto', 'poco', 'tanto', 'troppo', 'abbastanza', 'quasi', 'appena',
    'bene', 'male', 'meglio', 'peggio', 'così', 'come',
    'forse', 'probabilmente', 'certamente', 'sicuramente',
    'veramente', 'davvero', 'proprio', 'solo', 'soltanto', 'solamente',
    'insieme', 'separatamente', 'diversamente', 'altrimenti',
    'prima', 'dopo', 'poi', 'quindi', 'dunque', 'pertanto', 'perciò',
    'inoltre', 'infine', 'finalmente', 'soprattutto', 'specialmente',
    'particolarmente', 'principalmente', 'essenzialmente', 'naturalmente',
    'ovviamente', 'evidentemente', 'chiaramente', 'effettivamente',
    
    # === CONJUNCTIONS ===
    'e', 'ed', 'o', 'od', 'ma', 'però', 'tuttavia', 'eppure', 'anzi',
    'né', 'neanche', 'nemmeno', 'neppure',
    'che', 'se', 'perché', 'poiché', 'giacché', 'siccome', 'dato',
    'quando', 'mentre', 'finché', 'affinché', 'purché',
    'sebbene', 'benché', 'nonostante', 'malgrado',
    'come', 'quanto', 'qualora', 'laddove',
    'cioè', 'ossia', 'ovvero', 'oppure', 'infatti', 'invero',
    
    # === NUMBERS ===
    'uno', 'due', 'tre', 'quattro', 'cinque', 'sei', 'sette', 'otto', 'nove', 'dieci',
    'primo', 'secondo', 'terzo', 'quarto', 'quinto',
    'prima', 'seconda', 'terza', 'quarta', 'quinta',
    
    # === PARLIAMENTARY/FORMAL TERMS (non-distinctive) ===
    'presidente', 'signor', 'signora', 'signori', 'signore',
    'onorevole', 'onorevoli', 'colleghi', 'colleghe', 'collega',
    'ministro', 'ministri', 'sottosegretario', 'viceministro',
    'senatore', 'senatori', 'senatrice', 'senatrici',
    'deputato', 'deputati', 'deputata', 'deputate',
    'relatore', 'relatrice', 'relatori',
    'governo', 'parlamento', 'camera', 'senato', 'aula',
    'commissione', 'commissioni', 'comitato', 'comitati',
    'seduta', 'sedute', 'sessione', 'sessioni',
    'votazione', 'votazioni', 'voto', 'voti',
    'emendamento', 'emendamenti', 'subemendamento',
    'articolo', 'articoli', 'comma', 'commi', 'lettera', 'lettere',
    'legge', 'leggi', 'decreto', 'decreti', 'norma', 'norme', 'normativa',
    'disegno', 'proposta', 'proposte', 'mozione', 'mozioni',
    'ordine', 'giorno', 'punto', 'punti',
    'discussione', 'discussioni', 'dibattito', 'dibattiti',
    'intervento', 'interventi', 'parola', 'parole',
    'documento', 'documenti', 'testo', 'testi', 'allegato', 'allegati',
    'provvedimento', 'provvedimenti', 'misura', 'misure',
    'modifica', 'modifiche', 'modifica', 'integrazione', 'integrazioni',
    'attuazione', 'applicazione', 'disposizione', 'disposizioni',
    'termine', 'termini', 'proroga', 'proroghe',
    'approvazione', 'approvato', 'approvata', 'approvati', 'approvate',
    'rinvio', 'rinviato', 'rinviata',
    'favor', 'favore', 'favorevole', 'favorevoli',
    'contrario', 'contrari', 'contraria', 'contrarie',
    'astenuto', 'astenuti', 'astensione', 'astensioni',
    
    # === GENERIC TERMS ===
    'anno', 'anni', 'mese', 'mesi', 'giorno', 'giorni', 'settimana', 'settimane',
    'volta', 'volte', 'modo', 'modi', 'caso', 'casi', 'tipo', 'tipi',
    'parte', 'parti', 'punto', 'punti', 'fatto', 'fatti',
    'cosa', 'cose', 'questione', 'questioni', 'problema', 'problemi',
    'esempio', 'esempi', 'senso', 'sensi', 'base', 'basi',
    'tema', 'temi', 'argomento', 'argomenti', 'materia', 'materie',
    'rispetto', 'riguardo', 'confronto', 'merito',
    'paese', 'paesi', 'stato', 'stati', 'nazione', 'nazioni',
    'italia', 'italiano', 'italiana', 'italiani', 'italiane',
    'europa', 'europeo', 'europea', 'europei', 'europee', 'fratelli', 'fratello', 'fratelle', 'fratelli',
    'opposizioni',

    # === FORMAL/COURTESY EXPRESSIONS ===
    'ringrazio', 'ringraziare', 'ringraziamo', 'ringraziamento', 'ringraziamenti',
    'grazie', 'prego', 'cortesia', 'cortese', 'cortesemente',
    'odierna', 'odierno', 'odierni', 'odierne',
    'regolamento', 'regolamenti', 'regolamentare', 'regolamentari',
    'signori', 'signore', 'gentili', 'gentile', 'egregio', 'egregia',
    'illustre', 'illustri', 'preg.mo', 'spett.le',
    
    # === ADDITIONAL COMPREHENSIVE STOPWORDS ===
    'capigruppo', 'capogruppo',
    'abbastanza', 'accidenti', 'ahime', 'ahimè', 'allora', 'altrove',
    'ansa', 'anticipo', 'assai', 'attesa', 'attraverso', 'avanti',
    'aver', 'averlo', 'avente',
    'basta', 'ben', 'benissimo', 'brava', 'bravo', 'buono',
    'cento', 'chicchessia', 'cima', 'citta', 'città', 'cio',
    'codesta', 'codesti', 'codesto', 'cogli', 'coll', 'cominci',
    'comprare', 'comunque', 'concernente', 'conclusione', 
    'consecutivi', 'consecutivo', 'consiglio', 'contro',
    'cos', 'dappertutto', 'davanti', 'dentro', 'dirimpetto',
    'diventa', 'diventare', 'diventato', 'doppio', 'dov', 'dovra',
    'dovunque', 'ecc', 'ecco', 'entrambi', 'eppure', 'esser',
    'ex', 'faccia', 'facciamo', 'facciano', 'facciate', 'faccio',
    'facemmo', 'facesse', 'facessero', 'facessi', 'facessimo',
    'faceste', 'facesti', 'faceva', 'facevamo', 'facevano',
    'facevate', 'facevi', 'facevo', 'fai', 'farai', 'faranno',
    'farebbe', 'farebbero', 'farei', 'faremmo', 'faremo',
    'fareste', 'faresti', 'farete', 'farò', 'fece', 'fecero', 'feci',
    'fin', 'finche', 'fine', 'fino', 'forza', 'fra', 'frattempo',
    'futuro', 'generale', 'gente', 'gia', 'giacche', 'giu',
    'grande', 'gruppo', 'haha', 'ie', 'improvviso', 'inc',
    'indietro', 'infatti', 'insieme', 'intanto', 'intorno', 'invece',
    'lasciato', 'lato', 'lontano', 'lungo', 'luogo', 'là',
    'macche', 'magari', 'maggior', 'medesimo', 'mediante',
    'mila', 'miliardi', 'milioni', 'minimi', 'momento', 'mondo',
    'negl', 'nondimeno', 'nonsia', 'novanta', 'nuovi', 'nuovo',
    'ore', 'osi', 'ottanta', 'partendo', 'peccato', 'percio',
    'perfino', 'pero', 'persino', 'persone', 'piedi', 'pieno',
    'piglia', 'piu', 'piuttosto', 'po', 'pochissimo', 'poiche',
    'possa', 'possedere', 'posteriore', 'posto', 'preferibilmente',
    'presa', 'press', 'primo', 'promesso', 'puo', 'pure', 'purtroppo',
    'qua', 'quantunque', 'quel', 'quest', 'quinto',
    'realmente', 'recente', 'recentemente', 'registrazione',
    'relativo', 'riecco', 'salvo', 'sara', 'scola', 'scopo', 'scorso',
    'seguente', 'sembra', 'sembrare', 'sembrato', 'sembrava', 'sembri',
    'senza', 'sig', 'solito', 'spesso', 'stai', 'starai', 'staranno',
    'starebbe', 'starebbero', 'starei', 'staremmo', 'staremo',
    'stareste', 'staresti', 'starete', 'starò', 'stava', 'stavamo',
    'stavano', 'stavate', 'stavi', 'stavo', 'stemmo', 'stette',
    'stettero', 'stetti', 'stia', 'stiamo', 'stiano', 'stiate', 'sto',
    'subito', 'successivamente', 'successivo', 'sugl', 'talvolta',
    'terzo', 'th', 'titolo', 'tranne', 'trenta', 'triplo', 'uguali',
    'ulteriore', 'ultimo', 'uomo', 'vai', 'vale', 'verso', 'vicino',
    'vita',
}



# =============================================================================
# RHETORIC PATTERNS - Expanded keyword lists
# =============================================================================

# Keywords for populist rhetoric detection
POPULIST_KEYWORDS = [
    # People vs elite
    'popolo', 'gente', 'cittadini', 'italiani', 'paese reale',
    'gente comune', 'persone normali', 'persone oneste', 
    'famiglie', 'lavoratori', 'contribuenti', 'risparmiatori',
    'classe media', 'ceti popolari', 'maggioranza silenziosa',
    # Common sense
    'buonsenso', 'buon senso', 'senso comune',
    # Direct democracy
    'volontà popolare', 'sovranità popolare', 'voce del popolo',
]

# Keywords for anti-establishment rhetoric
ANTI_ESTABLISHMENT_KEYWORDS = [
    # Elites
    'élite', 'elite', 'casta', 'privilegiati', 'privilegio', 'privilegi',
    'palazzo', 'palazzi del potere', 'poteri forti', 'potere forte',
    'establishment', 'sistema', 'sistemico',
    # Corruption
    'oligarchia', 'oligarchi', 'lobby', 'lobbisti', 'lobbying',
    'clientela', 'clientelismo', 'clientelare',
    'corruzione', 'corrotto', 'corrotti', 'malaffare',
    'burocrazia', 'burocrati', 'burocratico',
    # Media
    'mainstream', 'media di regime', 'giornaloni',
]

# Keywords for institutional rhetoric
INSTITUTIONAL_KEYWORDS = [
    # Institutions
    'istituzione', 'istituzioni', 'istituzionale', 'istituzionali',
    'costituzione', 'costituzionale', 'costituzionali', 'carta costituzionale',
    'repubblica', 'repubblicano', 'repubblicana',
    # Democracy
    'democrazia', 'democratico', 'democratica', 'democratici',
    'stato di diritto', 'rule of law', 'certezza del diritto',
    # Rule following
    'legalità', 'legale', 'legittimità', 'legittimo',
    'regole', 'regola', 'regolamento', 'regolamenti',
    'procedura', 'procedure', 'procedurale', 'procedurali',
    'trasparenza', 'trasparente', 'accountability',
    # Bipartisanship
    'bipartisan', 'condivisione', 'condiviso', 'unitario', 'unità',
]

# Keywords for emotional rhetoric
EMOTIONAL_KEYWORDS = [
    # Outrage
    'vergogna', 'vergognoso', 'vergognosa',
    'scandalo', 'scandaloso', 'scandalosa',
    'inaccettabile', 'intollerabile', 'inammissibile',
    'indegno', 'indecente', 'indecoroso',
    'assurdo', 'assurdità', 'follia', 'folle',
    'incredibile', 'inconcepibile', 'incomprensibile',
    # Urgency
    'gravissimo', 'grave', 'gravi', 'gravità',
    'drammatico', 'drammatica', 'dramma', 'tragedia', 'tragico',
    'emergenza', 'urgenza', 'urgente', 'urgentissimo',
    'crisi', 'critico', 'critica', 'disastro', 'disastroso',
    # Fear
    'pericolo', 'pericoloso', 'pericolosa', 'minaccia', 'minaccioso',
    'devastante', 'catastrofe', 'catastrofico',
]

# Keywords for sovereignist/nationalist rhetoric
SOVEREIGNIST_KEYWORDS = [
    'sovranità', 'sovrano', 'sovranista', 'sovranismo',
    'patria', 'patriota', 'patriottico', 'patriottismo',
    'nazione', 'nazionale', 'nazionali', 'nazionalismo',
    'confini', 'confine', 'frontiera', 'frontiere',
    'identità', 'identitario', 'tradizione', 'tradizioni', 'tradizionale',
    'autodeterminazione', 'indipendenza', 'autonomia',
]

# Keywords for progressive/rights-based rhetoric
PROGRESSIVE_KEYWORDS = [
    'diritti', 'diritto', 'tutela', 'tutelare', 'garanzia', 'garantire',
    'uguaglianza', 'uguale', 'uguali', 'parità', 'pari opportunità',
    'inclusione', 'inclusivo', 'inclusiva', 'inclusività',
    'diversità', 'diverso', 'diversa', 'pluralismo', 'plurale',
    'discriminazione', 'discriminato', 'discriminata', 'antidiscriminazione',
    'minoranze', 'minoranza', 'vulnerabile', 'vulnerabili', 'fragile', 'fragili',
    'solidarietà', 'solidale', 'coesione', 'sociale',
    'ambiente', 'ambientale', 'ecologia', 'ecologico', 'sostenibilità', 'sostenibile',
    'clima', 'climatico', 'climatica', 'transizione',
]


# =============================================================================
# CRISIS & ALARM KEYWORDS (for Crisis ECG analysis)
# =============================================================================

CRISIS_KEYWORDS = {
    # Emergenza e pericolo
    'crisi', 'emergenza', 'pericolo', 'allarme', 'allerta', 'rischio',
    'minaccia', 'urgenza', 'urgente', 'urgentissimo', 'immediato',
    
    # Catastrofe e disastro
    'catastrofe', 'catastrofico', 'disastro', 'disastroso', 'tragedia', 'tragico',
    'dramma', 'drammatico', 'apocalisse', 'apocalittico', 'cataclisma',
    
    # Crollo e fallimento
    'collasso', 'crollo', 'fallimento', 'fallito', 'sfacelo', 'disfatta',
    'rovina', 'rovinoso', 'distruzione', 'devastazione', 'devastante',
    
    # Paura e panico
    'caos', 'caotico', 'panico', 'terrore', 'terrorizzante', 'paura',
    'spaventoso', 'orrore', 'orribile', 'incubo', 'nightmare',
    
    # Gravità
    'grave', 'gravissimo', 'critico', 'criticità', 'serio', 'serissimo',
    'preoccupante', 'allarmante', 'inquietante', 'sconvolgente',
    
    # Negatività estrema
    'vergogna', 'vergognoso', 'scandalo', 'scandaloso', 'indecente',
    'inaccettabile', 'intollerabile', 'inammissibile', 'assurdo',
    
    # Declino e perdita
    'baratro', 'abisso', 'precipizio', 'declino', 'decadenza', 'degrado',
    'peggioramento', 'deterioramento', 'aggravarsi', 'sprofondare',
    
    # Sofferenza
    'sofferenza', 'dolore', 'morte', 'morire', 'vittime', 'feriti',
    'malattia', 'epidemia', 'pandemia', 'contagio',
    
    # Economia critica
    'bancarotta', 'insolvenza', 'default', 'recessione', 'depressione',
    'inflazione', 'stangata', 'salasso', 'austerity',
    
    # Conflitto
    'guerra', 'conflitto', 'attacco', 'bombardamento', 'invasione',
    'violenza', 'scontro', 'rivolta', 'sommossa'
}


# =============================================================================
# SENTIMENT KEYWORDS (for Aspect-Based Sentiment Analysis)
# =============================================================================

POSITIVE_SENTIMENT_KEYWORDS = {
    'crescita', 'sviluppo', 'opportunità', 'successo', 'eccellenza',
    'miglioramento', 'progresso', 'innovazione', 'ottimismo', 'ripresa',
    'speranza', 'fiducia', 'entusiasmo', 'soddisfazione', 'orgoglio',
    'traguardo', 'conquista', 'vittoria', 'risultato', 'obiettivo',
    'positivo', 'favorevole', 'promettente', 'incoraggiante', 'brillante'
}

NEGATIVE_SENTIMENT_KEYWORDS = {
    'declino', 'peggioramento', 'fallimento', 'crisi', 'problema',
    'difficoltà', 'ostacolo', 'rischio', 'pericolo', 'minaccia',
    'preoccupazione', 'timore', 'paura', 'ansia', 'incertezza',
    'delusione', 'frustrazione', 'rabbia', 'indignazione', 'sconforto',
    'negativo', 'sfavorevole', 'allarmante', 'inquietante', 'devastante'
}


# =============================================================================
# POLARIZATION MARKERS (for "Us vs Them" analysis)
# =============================================================================

POLARIZATION_PRONOUNS = {
    'noi', 'loro', 'voi', 'nostro', 'nostra', 'nostri', 'nostre',
    'vostro', 'vostra', 'vostri', 'vostre'
}

ADVERSATIVE_TERMS = {
    'contro', 'nemici', 'nemico', 'avversari', 'avversario',
    'opposti', 'opposto', 'combattere', 'combattiamo', 'sconfiggere',
    'respingere', 'respingiamo', 'bloccare', 'fermare', 'impedire',
    'difendere', 'difendiamo', 'proteggere', 'proteggiamo',
    'minacciano', 'attaccano', 'vogliono', 'pretendono'
}

US_THEM_PATTERNS = [
    'noi contro loro', 'noi e loro', 'da una parte', 'dall\'altra parte',
    'chi sta con', 'chi sta contro', 'chi vuole', 'chi non vuole'
]


# =============================================================================
# OUTPUT
# =============================================================================

# Output directory for generated files
OUTPUT_DIR = "output"

# Webapp data file
WEBAPP_DATA_FILE = "webapp/data.json"
