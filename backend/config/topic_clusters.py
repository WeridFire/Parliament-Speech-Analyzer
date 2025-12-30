"""
Topic clusters configuration.
"""

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
        'label': 'Premierato e Autonomia',
        'keywords': [
            'premierato', 'autonomia differenziata', 'regionalismo', 'elezione diretta',
            'riforma costituzionale', 'presidenzialismo', 'semipresidenzialismo'
        ]
    },
    13: {
        'label': 'Riforme Elettorali',
        'keywords': [
            'legge elettorale', 'sistema elettorale', 'proporzionale', 'maggioritario',
            'bicameralismo', 'parlamento', 'collegi elettorali', 'quorum'
        ]
    }
}

# Set to None to use automatic K-Means clustering instead:
# TOPIC_CLUSTERS = None
