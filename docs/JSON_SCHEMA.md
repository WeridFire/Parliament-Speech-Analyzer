# Struttura JSON Output - Documentazione per Frontend

## File Generati
- `frontend/public/camera.json` - Dati Camera dei Deputati
- `frontend/public/senato.json` - Dati Senato della Repubblica

---

## Struttura Principale

```json
{
  "speeches": [...],           // Array di discorsi
  "deputies": [...],           // Array di deputati/senatori aggregati
  "deputies_by_period": {...}, // Aggregazioni per anno/mese
  "clusters": {...},           // Metadati dei topic cluster
  "rebels": [...],             // Top 15 "ribelli"
  "all_rebel_scores": {...},   // Score ribelle per ogni politico
  "stats": {...},              // Statistiche generali
  "analytics": {...}           // Analytics avanzate
}
```

---

## Sezione `analytics`

```json
{
  "analytics": {
    "global": {
      "identity": {...},
      "relations": {...},
      "temporal": {...},
      "qualitative": {...},
      "speaker_stats": {...}     // NUOVA SEZIONE
    },
    "by_year": {"2024": {...}, "2023": {...}},
    "by_month": {"2024-12": {...}, "2024-11": {...}},
    "available_periods": {
      "years": [2024, 2023],
      "months": ["2024-12", "2024-11", ...]
    }
  }
}
```

---

## Sezione `speaker_stats`

Questa sezione contiene statistiche dettagliate per ogni singolo politico.

### Struttura

```json
{
  "speaker_stats": {
    "by_speaker": {
      "ROSSI Mario": {
        "verbosity": {...},
        "linguistic": {...},
        "consistency": {...},
        "topic_leadership": {...},
        "intervention_patterns": {...},
        "vocabulary": {...},
        "network": {...}
      },
      "BIANCHI Anna": {...},
      ...
    },
    "rankings": {
      "most_verbose": [...],
      "most_concise": [...],
      "most_questions": [...],
      ...
    }
  }
}
```

---

### Dettaglio Metriche per Politico

#### 1. `verbosity` - Metriche di Prolissità

```typescript
interface Verbosity {
  avg_words_per_speech: number;       // Media parole per discorso
  avg_sentences_per_speech: number;   // Media frasi per discorso
  avg_words_per_sentence: number;     // Complessità sintattica
  total_words: number;                // Totale parole pronunciate
}
```

**Uso frontend**: Visualizzare quanto sono "verbosi" i politici.

---

#### 2. `linguistic` - Pattern Linguistici

```typescript
interface Linguistic {
  questions_per_1k_words: number;       // Stile interrogativo (Socratico)
  self_ref_per_1k_words: number;        // Autoreferenzialità ("io", "mio")
  negation_per_1k_words: number;        // Approccio negativo/critico
  future_markers_per_1k_words: number;  // Orientamento al futuro
  past_markers_per_1k_words: number;    // Orientamento al passato
  temporal_orientation: number;          // Ratio futuro/passato (>1 = futurista)
  data_citations_per_1k_words: number;  // Uso di dati/numeri
}
```

**Uso frontend**: 
- Radar chart del profilo linguistico
- Classificare politici come "visionari" vs "nostalgici"
- Identificare chi usa più dati concreti

---

#### 3. `consistency` - Coerenza Tematica

```typescript
interface Consistency {
  consistency_score: number;      // 0-100 (100 = sempre stesso tema)
  raw_variance: number;           // Varianza grezza degli embedding
  n_speeches: number;             // Numero discorsi analizzati
  interpretation: string;         // "very_consistent" | "consistent" | "moderate" | "variable" | "highly_variable"
}
```

**Uso frontend**: Identificare specialisti vs opportunisti.

---

#### 4. `topic_leadership` - Leadership di Tema

```typescript
interface TopicLeadership {
  topics_led: number[];           // ID dei topic "guidati"
  topics_led_labels: string[];    // Etichette dei topic guidati
  n_topics_led: number;           // Quanti topic guida
  dominant_topic: number | null;  // Topic principale
  dominant_topic_label: string;   // Etichetta topic principale
  topic_distances: {              // Distanza da ogni topic
    [topic_label: string]: number
  };
  n_speeches: number;
}
```

**Uso frontend**: 
- Mostrare "Chi è il campione di [Sanità]?"
- Badge "Leader" sui topic

---

#### 5. `intervention_patterns` - Pattern di Intervento

```typescript
interface InterventionPatterns {
  n_speeches: number;                      // Totale discorsi
  active_months: number;                   // Mesi con almeno 1 discorso
  total_months_in_data: number;            // Mesi totali nel dataset
  avg_speeches_per_month: number;          // Media mensile
  avg_speeches_per_active_month: number;   // Media nei mesi attivi
  regularity_score: number;                // 0-100 (100 = sempre attivo)
  burst_score: number;                     // 0-100 (100 = molto bursty)
  interpretation: string;                  // "very_regular" | "regular" | "moderate" | "sporadic" | "very_sporadic"
}
```

**Uso frontend**: 
- Identificare "workhorse" vs "occasionali"
- Heatmap attività nel tempo

---

#### 6. `vocabulary` - Ricchezza Lessicale

```typescript
interface Vocabulary {
  vocabulary_size: number;       // Parole uniche usate
  total_words: number;           // Parole totali
  type_token_ratio: number;      // TTR (unique/total)
  root_ttr: number;              // TTR normalizzato per confronto
  hapax_count: number;           // Parole usate solo una volta
  hapax_ratio: number;           // % hapax su vocabolario
  n_speeches: number;
  richness_score: number;        // Score 0-100ish
  interpretation: string;        // "very_rich" | "rich" | "moderate" | "limited" | "very_limited"
}
```

**Uso frontend**: Indicatore di "cultura" e varietà espressiva.

---

#### 7. `network` - Rete di Menzioni

```typescript
interface Network {
  party: string;                       // Partito del politico
  out_degree: number;                  // Quante persone diverse menziona
  in_degree: number;                   // Da quanti viene menzionato
  total_mentions_given: number;        // Totale menzioni fatte
  total_mentions_received: number;     // Totale menzioni ricevute
  top_mentioned: [string, number][];   // Top 5 menzionati [(nome, count), ...]
  top_mentioners: [string, number][];  // Top 5 che lo menzionano
  n_speeches: number;
  network_score: number;               // Score combinato (out + in*2)
}
```

**Uso frontend**: 
- Grafo interattivo delle menzioni
- Identificare "opinion leader"

---

### Rankings Aggregati

```typescript
interface Rankings {
  most_verbose: [string, number][];           // [(speaker, avg_words), ...]
  most_concise: [string, number][];
  most_questions: [string, number][];         // Più interrogativi
  most_self_referential: [string, number][];  // Più autoreferenziali
  most_negative: [string, number][];          // Più negazioni
  most_future_oriented: [string, number][];   // Più orientati al futuro
  most_data_driven: [string, number][];       // Più uso di dati
  most_consistent: [string, number][];        // Più coerenti
  most_variable: [string, number][];          // Meno coerenti
  most_regular: [string, number][];           // Più regolari
  richest_vocabulary: [string, number][];     // Vocabolario più ricco
  most_connected: [string, number][];         // Più connessi nel network
}
```

Ogni ranking contiene **top 10** politici per quella metrica.

---

## Esempio Utilizzo Frontend

### Mostrare profilo politico

```javascript
const speaker = data.analytics.global.speaker_stats.by_speaker["ROSSI Mario"];

// Card verbosità
<StatCard 
  title="Prolissità"
  value={speaker.verbosity.avg_words_per_speech}
  unit="parole/discorso"
/>

// Orientamento temporale
const orientation = speaker.linguistic.temporal_orientation > 1 
  ? "Visionario 🚀" 
  : "Nostalgico 📜";

// Badge topic leadership
speaker.topic_leadership.topics_led_labels.map(topic => (
  <Badge key={topic}>Leader: {topic}</Badge>
))
```

### Mostrare ranking

```javascript
const rankings = data.analytics.global.speaker_stats.rankings;

// Top 10 più prolissi
rankings.most_verbose.map(([name, score]) => (
  <RankingRow name={name} score={score} />
))
```

---

## Note Tecniche

- Tutti i valori `per_1k_words` sono normalizzati per 1000 parole per permettere confronti equi
- I `score` (consistency, regularity, richness) sono su scala 0-100
- Le `interpretation` sono stringhe pronte per l'UI (es. mostrare "Molto Consistente" per "very_consistent")
- I `topic_distances` usano le etichette come chiavi per facilità d'uso
