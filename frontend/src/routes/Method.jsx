import { Page } from '../layout/AppShell';
import { PageHeader } from '../ui';

/**
 * Methodological note.
 *
 * The old app scattered its caveats across tooltips and a modal. Collecting
 * them on one page matters here: several metrics are easy to over-read, and
 * the two chambers are not directly comparable.
 */
export default function Method() {
  return (
    <Page className="max-w-[820px]">
      <PageHeader
        eyebrow="Nota metodologica"
        title="Come sono calcolate le metriche"
        description="Tutte le misure derivano dal testo degli interventi in Assemblea. Nessuna deriva dai voti o dalle presenze."
      />

      <div className="mt-10 flex flex-col gap-10">
        <Section title="Fonte dei dati">
          <p>
            I resoconti stenografici delle sedute d&apos;Assemblea vengono raccolti da{' '}
            <em>camera.it</em> e <em>senato.it</em> per la XIX legislatura. Ogni intervento è
            attribuito a chi lo pronuncia e al suo gruppo parlamentare; i nomi sono verificati
            contro l&apos;elenco ufficiale dei parlamentari in carica.
          </p>
          <p>
            Sono esclusi gli interventi della Presidenza, quelli puramente procedurali e quelli
            sotto le 30 parole.
          </p>
        </Section>

        <Section title="Collocazione tematica">
          <p>
            Ogni intervento è rappresentato come vettore da un modello multilingue di similarità
            semantica, poi proiettato su due dimensioni per la mappa. Le quattordici aree tematiche
            non sono cluster scoperti automaticamente: sono definite a priori tramite liste di
            parole chiave, e ogni intervento è assegnato all&apos;area con la similarità più alta.
          </p>
          <p>
            La distribuzione risultante è fortemente sbilanciata. Nei dati della Camera,
            «Premierato e Autonomia» e «Riforme Elettorali» insieme raccolgono circa il 63% degli
            interventi, mentre «Agricoltura» ne conta un centinaio: l&apos;assegnazione semantica
            tende ad attrarre il linguaggio istituzionale e procedurale verso poche aree. I
            confronti fra temi vanno letti con questa avvertenza.
          </p>
        </Section>

        <Section title="Le metriche principali">
          <Definition term="Indipendenza tematica">
            Quota di interventi di un parlamentare che ricadono fuori dall&apos;area tematica
            prevalente del suo gruppo. Misura la distanza dall&apos;agenda del gruppo, non il
            dissenso politico.
          </Definition>
          <Definition term="Coesione interna">
            Quanto sono ravvicinati fra loro gli interventi di un gruppo nello spazio semantico.
            Espressa su scala 0–1.
          </Definition>
          <Definition term="Affinità">
            Similarità fra i baricentri semantici di due gruppi. Indica sovrapposizione di
            linguaggio e di temi, non vicinanza politica.
          </Definition>
          <Definition term="Indice di generalismo">
            Entropia della distribuzione tematica, normalizzata su scala 0–100. Valori alti
            indicano un intervento su molte aree, valori bassi una forte specializzazione.
          </Definition>
          <Definition term="Bipartisanship">
            Per ciascun tema, quanto equilibrata è la partecipazione fra schieramenti. Un tema è
            bipartisan quando entrambi gli schieramenti vi intervengono in misura comparabile.
          </Definition>
          <Definition term="Indice Gulpease">
            Misura di leggibilità tarata sull&apos;italiano. Sotto 55 il testo è considerato
            difficile per un lettore con licenza media.
          </Definition>
          <Definition term="Polarizzazione">
            Frequenza di contrapposizioni «noi/loro», avversative e formule oppositive per mille
            parole. Riguarda la forma del linguaggio, non il contenuto delle posizioni.
          </Definition>
        </Section>

        <Section title="Limiti da tenere presenti">
          <ul className="ml-4 list-disc [&>li]:mt-2">
            <li>
              <strong className="text-ink">Le due Camere non sono confrontabili</strong> a parità di
              condizioni: le finestre temporali coperte e il numero di interventi raccolti
              differiscono sensibilmente.
            </li>
            <li>
              <strong className="text-ink">Molte metriche hanno soglie minime.</strong> A seconda
              dell&apos;indicatore servono almeno due, tre o cinque interventi: un pannello vuoto
              di norma significa «sotto soglia», non «errore».
            </li>
            <li>
              <strong className="text-ink">Il sentiment è lessicale.</strong> Deriva dal conteggio
              di termini positivi e negativi e non riconosce ironia, citazioni o negazioni
              complesse.
            </li>
            <li>
              <strong className="text-ink">Parlare non è deliberare.</strong> Nessuna metrica qui
              misura voti, presenze o esiti legislativi.
            </li>
          </ul>
        </Section>

        <Section title="Colore e leggibilità">
          <p>
            I colori delle serie nei grafici non sono i colori dei partiti. I colori istituzionali
            dei gruppi non superano le verifiche di distinguibilità: alcune coppie — per esempio il
            verde della Lega e il rosso del PD — risultano quasi identiche a chi ha una
            deficienza della visione cromatica. I colori di partito compaiono quindi solo come
            pastiglie accanto a un&apos;etichetta testuale, mentre le serie dei grafici usano una
            scala verificata e limitata nel numero di elementi.
          </p>
          <p>
            Per lo stesso motivo la mappa non colora quattordici temi contemporaneamente: evidenzia
            al massimo tre elementi per volta e mantiene il resto come contesto neutro.
          </p>
        </Section>
      </div>
    </Page>
  );
}

function Section({ title, children }) {
  return (
    <section>
      <h2 className="text-h2">{title}</h2>
      <div className="mt-3 flex flex-col gap-3 text-body leading-relaxed text-secondary">
        {children}
      </div>
    </section>
  );
}

function Definition({ term, children }) {
  return (
    <div className="border-l-2 border-rule pl-4">
      <dt className="text-h3">{term}</dt>
      <dd className="mt-1 text-body text-secondary">{children}</dd>
    </div>
  );
}
