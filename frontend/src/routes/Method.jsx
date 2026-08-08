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
            L&apos;elenco delle sedute d&apos;Assemblea e l&apos;anagrafe dei parlamentari
            provengono dai dati aperti ufficiali (<em>dati.camera.it</em> e{' '}
            <em>dati.senato.it</em>) per la XIX legislatura. Il testo degli interventi viene poi
            letto dai resoconti stenografici pubblicati su <em>camera.it</em> e <em>senato.it</em>.
          </p>
          <p>
            Partire dall&apos;elenco ufficiale significa sapere quante sedute <em>dovrebbero</em>{' '}
            esserci: ogni elaborazione confronta le sedute note con quelle effettivamente raccolte,
            così una raccolta incompleta è un numero visibile e non un archivio silenziosamente più
            piccolo.
          </p>
          <p>
            Ogni intervento è attribuito a chi lo pronuncia confrontando il nome con l&apos;anagrafe
            ufficiale. Quando più parlamentari condividono il cognome e il gruppo non basta a
            distinguerli, l&apos;attribuzione viene marcata come incerta anziché risolta in
            silenzio. Sono esclusi gli interventi della Presidenza, quelli puramente procedurali e
            quelli sotto le 30 parole.
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
            L&apos;assegnazione ha una soglia minima. Un intervento che non somiglia abbastanza a
            nessuna delle aree resta <strong className="text-ink">non classificato</strong> invece
            di essere attribuito all&apos;area meno lontana: senza questa soglia ogni intervento
            riceve comunque un tema, comprese le comunicazioni di servizio che non parlano di
            nulla. Ogni intervento porta con sé anche un margine di confidenza, cioè la distanza fra
            la prima e la seconda area: un margine basso indica un&apos;assegnazione fragile.
          </p>
          <p>
            La distribuzione risultante resta sbilanciata: l&apos;assegnazione semantica tende ad
            attrarre il linguaggio istituzionale e procedurale verso poche aree. I confronti fra
            temi vanno letti con questa avvertenza.
          </p>
        </Section>

        <Section title="Le metriche principali">
          <Definition term="Indipendenza tematica">
            Quota di interventi di un parlamentare che ricadono fuori dall&apos;area tematica
            prevalente del suo gruppo, calcolata su almeno cinque interventi. Misura la distanza
            dall&apos;agenda del gruppo, non il dissenso politico: chi siede in una commissione
            diversa dalla maggioranza dei colleghi di partito ottiene un valore alto senza aver
            mai espresso disaccordo.
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
            Frequenza di contrapposizioni «noi/loro», avversative e formule oppositive ogni mille
            parole. Riguarda la forma del linguaggio, non il contenuto delle posizioni: citare un
            avversario per contestarlo conta quanto sostenerlo.
          </Definition>
          <Definition term="Valori grezzi e percentili">
            Le metriche costruite su lessici di marcatori sono pubblicate in due forme. Il{' '}
            <em>valore grezzo</em> ha un&apos;unità dichiarata — marcatori ogni mille parole — e non
            ha un tetto. Il <em>percentile</em> indica la posizione rispetto agli altri
            parlamentari dello stesso insieme di dati, ed è ciò che determina la lunghezza delle
            barre e l&apos;ordine delle classifiche. Le etichette «bassa», «media» e «alta» si
            riferiscono al percentile, non a soglie assolute.
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
              dell&apos;indicatore servono almeno tre o cinque interventi per parlamentare: un
              pannello vuoto di norma significa «sotto soglia», non «errore».
            </li>
            <li>
              <strong className="text-ink">Non tutte le metriche esistono per ogni periodo.</strong>{' '}
              Le misure che descrivono un cambiamento nel tempo, o che richiedono un campione ampio
              — entropia tematica, termini distintivi, affinità fra gruppi — non vengono ricalcolate
              su una singola mensilità: su poche decine di interventi misurerebbero il campione, non
              il discorso. In quei casi la pagina mostra il dato complessivo.
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
