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
            parole chiave, e ogni intervento è assegnato all&apos;area più simile.
          </p>
          <p>
            Il confronto avviene dopo aver sottratto la componente comune a tutti gli interventi.
            Senza questa correzione le descrizioni dal suono più «istituzionale» attiravano tutto:
            due sole aree, Premierato e Riforme elettorali, raccoglievano il 62% degli interventi
            della Camera. Su un campione di interventi le cui parole chiave indicano chiaramente un
            tema, l&apos;accordo con l&apos;assegnazione è passato dal 51% al 72%.
          </p>
          <p>
            L&apos;assegnazione ha una soglia minima. Un intervento che non somiglia abbastanza a
            nessuna delle aree — tipicamente richiami al regolamento e scambi di cortesia — resta{' '}
            <strong className="text-ink">non classificato</strong> invece di essere attribuito
            all&apos;area meno lontana. Ogni intervento porta con sé anche un margine di confidenza,
            la distanza fra la prima e la seconda area: un margine basso indica
            un&apos;assegnazione fragile.
          </p>
        </Section>

        <Section title="Le metriche principali">
          <Definition term="Profilo tematico e sovra-rappresentazione">
            Quota degli interventi di un gruppo dedicata a ciascuna area, confrontata con la media
            dell&apos;Aula. Il rapporto fra le due dice su cosa il gruppo insiste più degli altri:
            2 significa il doppio della media, 0,5 la metà.
          </Definition>
          <Definition term="Vocabolario distintivo">
            Parole che un gruppo (o uno schieramento, o un tema) usa più del resto dell&apos;Aula,
            misurate con il log-odds ratio con prior informativo: una parola conta solo se la
            differenza è grande rispetto a quanto potrebbe essere dovuta al caso, e se compare in
            almeno cinque interventi diversi. Sono esclusi i nomi dei gruppi e il lessico
            procedurale.
          </Definition>
          <Definition term="Maggioranza e opposizione">
            La maggioranza comprende i gruppi che sostengono il Governo e i membri del Governo;
            l&apos;opposizione tutti gli altri gruppi, escluso il Misto. Un tema «appartiene» a uno
            schieramento quando questo gli dedica almeno 1,4 volte la quota dei propri interventi
            che gli dedica l&apos;altro. Si confrontano quote e non conteggi, perché
            l&apos;opposizione interviene di più in assoluto.
          </Definition>
          <Definition term="Affinità e omogeneità">
            L&apos;affinità è la somiglianza fra i baricentri semantici di due gruppi;
            l&apos;omogeneità è la somiglianza media fra gli interventi di uno stesso gruppo. Entrambe
            sono calcolate dopo aver rimosso la componente comune, per cui 0 equivale a due
            interventi presi a caso. Indicano sovrapposizione di linguaggio e di temi, non vicinanza
            politica.
          </Definition>
          <Definition term="Applausi e proteste">
            Le note del resoconto — «(Applausi dei deputati del gruppo …)», «(Proteste …)» — dicono
            come gli altri gruppi hanno reagito a un intervento. Ogni intervento conta una volta per
            ciascun gruppo che lo applaude. Al Senato le note riportano solo «(Applausi)»: si può
            misurare quanto un gruppo viene applaudito, non da chi.
          </Definition>
          <Definition term="Chi nomina chi">
            Frequenza con cui gli interventi di ciascun gruppo nominano un elenco di leader, ministri
            e capi di governo stranieri, ogni 100 interventi. Una menzione non dice se è una critica
            o un sostegno.
          </Definition>
          <Definition term="Indice di generalismo">
            Entropia della distribuzione tematica, normalizzata su scala 0–100 rispetto alle
            quattordici aree. Calcolato solo per chi ha almeno 20 interventi classificati: con pochi
            interventi l&apos;entropia è sottostimata per costruzione.
          </Definition>
          <Definition term="Varietà lessicale">
            MATTR, il rapporto fra parole diverse e parole totali calcolato su finestre di 500
            parole e poi mediato. A differenza del semplice rapporto, non premia chi parla meno.
          </Definition>
          <Definition term="Indice Gulpease">
            Misura di leggibilità tarata sull&apos;italiano. Sotto 55 il testo è considerato
            difficile per un lettore con licenza media. Le frasi sono quelle del resoconto: la
            punteggiatura è degli stenografi.
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
            barre e l&apos;ordine delle classifiche.
          </Definition>
        </Section>

        <Section title="Cosa è stato tolto, e perché">
          <ul className="ml-4 list-disc [&>li]:mt-2">
            <li>
              <strong className="text-ink">Sentiment lessicale.</strong> Contava 25 parole
              «positive» e 25 «negative», fra cui «problema», «rischio» e «obiettivo»: le differenze
              fra temi erano indistinguibili da zero e le classifiche erano guidate da chi aveva un
              solo intervento.
            </li>
            <li>
              <strong className="text-ink">Retorica populista e anti-establishment.</strong> I
              lessici contenevano parole neutre in Parlamento, come «cittadini» e «sistema».
            </li>
            <li>
              <strong className="text-ink">Indice di crisi, deriva semantica, cambi di tema,
              coerenza, fazioni.</strong> Misuravano soprattutto il tema discusso o la quantità di
              interventi, non ciò che dichiaravano di misurare.
            </li>
            <li>
              <strong className="text-ink">Indipendenza tematica.</strong> Dipendeva dal tema
              prevalente del gruppo, che con l&apos;assegnazione precedente era quasi sempre lo
              stesso per tutti.
            </li>
          </ul>
        </Section>

        <Section title="Limiti da tenere presenti">
          <ul className="ml-4 list-disc [&>li]:mt-2">
            <li>
              <strong className="text-ink">Le due Camere non sono confrontabili</strong> a parità di
              condizioni: i periodi coperti e il numero di interventi raccolti differiscono.
            </li>
            <li>
              <strong className="text-ink">Molte metriche hanno soglie minime.</strong> A seconda
              dell&apos;indicatore servono da 5 a 20 interventi per parlamentare: un pannello vuoto di
              norma significa «sotto soglia», non «errore».
            </li>
            <li>
              <strong className="text-ink">Non tutte le metriche esistono per ogni periodo.</strong>{' '}
              Le misure che richiedono un campione ampio — affinità fra gruppi, vocabolario
              distintivo, confronto fra schieramenti — non vengono ricalcolate su una singola
              mensilità. In quei casi la pagina mostra il dato complessivo e lo segnala.
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
