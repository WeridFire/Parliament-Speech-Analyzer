"""
Keywords for text analysis (Rhetoric, Sentiment, Crisis, Polarization).
"""

# =============================================================================
# RHETORIC PATTERNS
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
# CRISIS & ALARM KEYWORDS
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
# SENTIMENT KEYWORDS
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
# POLARIZATION MARKERS
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
