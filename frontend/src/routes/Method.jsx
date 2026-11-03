import { Page } from '../layout/AppShell';
import { PageHeader } from '../ui';

/**
 * Methodological note, written for the site's readers: how the numbers are
 * produced and how to read them. Several metrics are easy to over-read, and
 * the two chambers are not directly comparable, so the caveats live here in
 * one place rather than scattered across tooltips.
 */
export default function Method() {
  return (
    <Page className="max-w-[820px]">
      <PageHeader
        eyebrow="Nota metodologica"
        title="Come nascono i numeri"
        description="Dalla raccolta dei resoconti al calcolo di ogni misura: cosa viene analizzato, come, e come leggere i risultati. Tutte le misure derivano dal testo degli interventi in Aula, nessuna dai voti o dalle presenze."
      />

      <div className="mt-10 flex flex-col gap-10">
        <Section title="Da dove vengono i dati">
          <p>
            L&apos;elenco delle sedute dell&apos;Assemblea e l&apos;anagrafe dei parlamentari della
            XIX legislatura provengono dai dati aperti ufficiali, <em>dati.camera.it</em> e{' '}
            <em>dati.senato.it</em>. Il testo degli interventi è letto dai resoconti stenografici
            pubblicati su <em>camera.it</em> e <em>senato.it</em>. Il periodo coperto da ciascuna
            Camera è indicato in cima alle pagine di analisi.
          </p>
          <p>
            Partire dall&apos;elenco ufficiale permette di sapere quante sedute dovrebbero esserci e
            di controllare che siano state raccolte tutte.
          </p>
        </Section>

        <Section title="Dai resoconti agli interventi">
          <p>
            Un <strong className="text-ink">intervento</strong> è un blocco di testo pronunciato da
            un parlamentare o da un membro del Governo senza che altri prendano la parola. Ogni
            intervento è attribuito a chi lo pronuncia confrontando il nome riportato nel resoconto
            con l&apos;anagrafe ufficiale; quando più parlamentari hanno lo stesso cognome e il
            gruppo non basta a distinguerli, l&apos;attribuzione è segnata come incerta.
          </p>
          <p>
            Sono esclusi gli interventi di chi presiede la seduta e quelli sotto le 30 parole, che
            sono quasi sempre battute procedurali. Dal testo usato per le analisi vengono tolte le
            formule di rito («Grazie, Presidente», «Onorevoli colleghi»); il testo mostrato nella
            mappa resta quello originale.
          </p>
          <p>
            I gruppi parlamentari compaiono con nomi diversi nelle due Camere e nelle note dei
            resoconti («PD-IDP», «Partito Democratico - Italia Democratica e Progressista»): sono
            ricondotti a un unico nome. Al Senato, se un intervento non riporta il gruppo, si usa
            quello abituale del senatore.
          </p>
          <p>
            Per i confronti fra schieramenti, la <strong className="text-ink">maggioranza</strong>{' '}
            comprende Fratelli d&apos;Italia, Lega, Forza Italia, Noi Moderati e i membri del
            Governo; l&apos;<strong className="text-ink">opposizione</strong> comprende Partito
            Democratico, MoVimento 5 Stelle, Alleanza Verdi e Sinistra, Azione, Italia Viva e
            +Europa. Il Gruppo misto e le componenti delle minoranze linguistiche e delle autonomie
            restano a parte.
          </p>
        </Section>

        <Section title="Come si assegna un tema">
          <p>
            Un modello linguistico multilingue trasforma ogni intervento in un vettore numerico:
            interventi che parlano delle stesse cose ottengono vettori vicini. La mappa semantica
            mostra questi vettori ridotti a due dimensioni, per cui due punti vicini sulla mappa
            sono due interventi simili nel contenuto.
          </p>
          <p>
            Le quattordici aree tematiche sono definite in anticipo, ciascuna da un nome e da un
            elenco di parole chiave. Anche queste descrizioni sono trasformate in vettori, e ogni
            intervento è assegnato all&apos;area la cui descrizione gli somiglia di più. Prima del
            confronto si sottrae ciò che tutti gli interventi hanno in comune — il registro
            generico del linguaggio parlamentare — così che a contare sia l&apos;argomento e non
            il tono istituzionale.
          </p>
          <p>
            Un intervento che non somiglia abbastanza a nessuna area resta{' '}
            <strong className="text-ink">non classificato</strong>: accade a circa un intervento su
            dieci, soprattutto richiami al regolamento e scambi di cortesia. Per ogni intervento si
            conserva anche la distanza fra l&apos;area scelta e la seconda più vicina: quando è
            piccola, il dettaglio dell&apos;intervento segnala l&apos;assegnazione come{' '}
            <em>incerta</em>.
          </p>
        </Section>

        <Section title="Cosa misura ogni analisi">
          <Definition term="Identità · profilo tematico">
            La quota degli interventi di un gruppo dedicata a ciascuna area, confrontata con la
            media dell&apos;Aula. Il rapporto fra le due dice su cosa il gruppo insiste più degli
            altri: un rapporto di 2 significa il doppio della media, 0,5 la metà. Nella mappa di
            calore il rosso indica i temi su cui il gruppo insiste di più, il blu quelli che
            trascura.
          </Definition>
          <Definition term="Identità · vocabolario distintivo">
            Le parole che un gruppo usa più del resto dell&apos;Aula. Per ogni sostantivo, aggettivo
            e nome proprio si confronta la frequenza nel gruppo con quella negli altri gruppi,
            tenendo conto di quanto la differenza potrebbe essere dovuta al caso (tecnicamente, un
            log-odds ratio con prior informativo). Una parola entra nell&apos;elenco solo se il
            gruppo la usa in almeno cinque interventi diversi. I nomi dei gruppi e il lessico
            procedurale («emendamento», «ordine del giorno») sono esclusi. Lo stesso metodo produce
            le parole di ogni tema e di ogni schieramento.
          </Definition>
          <Definition term="Identità · indice di generalismo">
            Quanto un parlamentare o un gruppo distribuisce i propri interventi fra le aree, su una
            scala da 0 (una sola area) a 100 (tutte le aree in egual misura). È calcolato solo per
            chi ha almeno 20 interventi classificati: con pochi interventi chiunque sembrerebbe
            specializzato.
          </Definition>
          <Definition term="Temi">
            Per ogni area: i parlamentari che vi intervengono più spesso (con almeno tre interventi
            sul tema) e quale parte dei loro interventi complessivi vi dedicano; e, per ogni
            gruppo, quanto è presente sul tema rispetto al suo peso nel dibattito — ×1 vuol dire in
            proporzione, ×2 il doppio.
          </Definition>
          <Definition term="Maggioranza e opposizione">
            Per ogni area si confronta la quota dei propri interventi che ciascuno schieramento le
            dedica. Si usano le quote e non i numeri assoluti perché i due schieramenti non
            prendono la parola con la stessa frequenza. Un tema è attribuito a uno schieramento
            quando questo gli dedica almeno 1,4 volte l&apos;attenzione dell&apos;altro; altrimenti
            è condiviso.
          </Definition>
          <Definition term="Relazioni · affinità e omogeneità">
            L&apos;affinità fra due gruppi è la somiglianza fra i loro interventi medi; l&apos;omogeneità
            di un gruppo è quanto i suoi interventi si somigliano fra loro. Entrambe sono calcolate
            dopo aver tolto la componente comune a tutti gli interventi, per cui 0 equivale alla
            somiglianza fra due interventi qualsiasi. Indicano sovrapposizione di linguaggio e di
            temi, non vicinanza politica, e un gruppo che parla di pochi argomenti risulta più
            omogeneo.
          </Definition>
          <Definition term="Relazioni · ponti fra gruppi">
            Le coppie di parlamentari di gruppi diversi i cui interventi, in media, si somigliano di
            più. Sono considerati solo parlamentari con almeno 10 interventi; il simbolo ⇄ indica
            una coppia che attraversa maggioranza e opposizione.
          </Definition>
          <Definition term="Applausi e proteste">
            I resoconti annotano le reazioni dell&apos;Aula: «(Applausi dei deputati del gruppo …)»,
            «(Proteste …)», «(Commenti …)». Ogni intervento conta una volta per ciascun gruppo che
            lo applaude o lo contesta. La matrice «chi applaude chi» esclude gli applausi del
            proprio gruppo, che sono la norma. I resoconti del Senato riportano solo «(Applausi)»
            senza indicare il gruppo: per il Senato si può dire quanto un gruppo viene applaudito,
            non da chi.
          </Definition>
          <Definition term="Chi nomina chi">
            Quante volte, ogni 100 interventi, ciascun gruppo nomina un elenco di leader di partito,
            ministri, il Presidente della Repubblica e alcuni capi di governo stranieri. Un nome è
            riconosciuto dal cognome scritto con l&apos;iniziale maiuscola, un intervento conta una
            volta per figura, e chi parla non viene contato quando nomina se stesso. Una menzione non
            dice se si tratta di una critica o di un sostegno.
          </Definition>
          <Definition term="Tendenze">
            La quota degli interventi di ogni mese dedicata a ciascuna area, e il numero di
            interventi al mese per schieramento. Si usano le quote perché il numero di sedute cambia
            molto da un mese all&apos;altro. Le tendenze coprono sempre l&apos;intero periodo
            disponibile.
          </Definition>
          <Definition term="Linguaggio · leggibilità">
            L&apos;indice Gulpease, tarato sull&apos;italiano, combina la lunghezza delle parole e
            quella delle frasi: sotto 55 un testo è difficile per chi ha la licenza media, sopra 80
            è facile. Le frasi sono quelle del resoconto, la cui punteggiatura è decisa dagli
            stenografi; le differenze fra gruppi sono piccole e vanno lette come tali.
          </Definition>
          <Definition term="Linguaggio · polarizzazione">
            Quante contrapposizioni «noi/loro», espressioni avversative («contro», «nemici») e
            formule oppositive compaiono ogni mille parole. Riguarda la forma del linguaggio, non le
            posizioni: citare un avversario per contestarlo conta quanto sostenerlo. Il valore
            mostrato è la frequenza; la lunghezza della barra è il percentile, cioè la posizione
            rispetto agli altri parlamentari. Nelle classifiche entrano solo parlamentari con almeno
            10 interventi.
          </Definition>
          <Definition term="Parlamentari">
            Per chi ha almeno 5 interventi nel periodo: numero di interventi e di giornate in cui ha
            preso la parola, mesi con almeno un intervento, lunghezza media degli interventi, temi
            principali e reazioni ricevute da altri gruppi. La varietà lessicale è misurata come
            rapporto fra parole diverse e parole totali su finestre di 500 parole (MATTR), così da
            non favorire chi parla meno; richiede almeno 1.000 parole. Il profilo linguistico
            riporta domande, uso della prima persona, negazioni, dati citati (percentuali, importi,
            cifre), lunghezza delle frasi e varietà lessicale, ciascuno su una scala fissa.
          </Definition>
        </Section>

        <Section title="Periodi e soglie minime">
          <p>
            Ogni analisi può essere ristretta a un anno o a un mese. Alcune misure hanno però
            bisogno di molti interventi per essere affidabili: l&apos;affinità fra gruppi ne
            richiede almeno 200 nel periodo, il profilo tematico e il confronto fra schieramenti
            150, temi, applausi e menzioni 100, linguaggio e profili individuali 50. Quando il
            periodo scelto non basta, la pagina mostra il dato dell&apos;intero periodo disponibile
            e lo segnala con un avviso.
          </p>
          <p>
            Allo stesso modo molte classifiche richiedono un minimo di interventi per parlamentare,
            indicato sotto ciascun pannello: un elenco vuoto di norma significa «sotto soglia», non
            «errore».
          </p>
        </Section>

        <Section title="Limiti da tenere presenti">
          <ul className="ml-4 list-disc [&>li]:mt-2">
            <li>
              <strong className="text-ink">Le due Camere non sono confrontabili</strong> a parità di
              condizioni: i periodi coperti e il numero di interventi raccolti differiscono.
            </li>
            <li>
              <strong className="text-ink">Il tema è assegnato in automatico.</strong> Un intervento
              che tocca più argomenti riceve una sola area, e il modello legge circa le prime cento
              parole di ogni intervento.
            </li>
            <li>
              <strong className="text-ink">Le misure lessicali contano parole, non significati.</strong>{' '}
              Non riconoscono ironia, citazioni o negazioni.
            </li>
            <li>
              <strong className="text-ink">Parlare non è deliberare.</strong> Nessuna metrica misura
              voti, presenze o esiti legislativi.
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
