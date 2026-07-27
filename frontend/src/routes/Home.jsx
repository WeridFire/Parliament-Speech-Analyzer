import { Link } from 'react-router';
import { ArrowRight, BarChart3, Github, Map as MapIcon, Users } from 'lucide-react';
import { Page } from '../layout/AppShell';

/**
 * Landing page. Sets the register for the whole site: serif display type,
 * hairline rules, no gradients, no emoji, generous whitespace.
 */
export default function Home() {
  return (
    <Page>
      <section className="max-w-3xl">
        <p className="text-label text-muted">XIX LEGISLATURA · CAMERA E SENATO</p>

        <h1 className="mt-3 font-serif text-[clamp(2rem,5vw,3.25rem)] leading-[1.08] font-semibold tracking-tight text-balance">
          Come parla il Parlamento italiano
        </h1>

        <p className="mt-5 max-w-2xl text-[0.9375rem] leading-relaxed text-secondary">
          Analisi quantitativa dei resoconti stenografici delle sedute d&apos;Assemblea. Ogni
          intervento viene collocato in uno spazio semantico, attribuito a una delle quattordici
          aree tematiche e aggregato per gruppo parlamentare, tema e periodo.
        </p>

        <div className="mt-8 flex flex-wrap items-center gap-3">
          <Link
            to="/mappa"
            className="inline-flex items-center gap-2 rounded-sm bg-accent px-4 py-2.5 text-body font-medium text-accent-ink no-underline transition-colors duration-150 hover:bg-accent-hover"
          >
            Apri la mappa semantica
            <ArrowRight size={15} aria-hidden="true" />
          </Link>
          <Link
            to="/analisi"
            className="inline-flex items-center gap-2 rounded-sm border border-rule px-4 py-2.5 text-body font-medium text-ink no-underline transition-colors duration-150 hover:border-rule-strong hover:bg-hover"
          >
            Vai alle analisi
          </Link>
        </div>
      </section>

      <section className="mt-16 border-t border-rule pt-10">
        <h2 className="text-h2">Tre modi di leggere i dati</h2>
        <div className="mt-6 grid gap-px overflow-hidden rounded-md border border-rule bg-rule sm:grid-cols-3">
          <Feature
            icon={MapIcon}
            title="Mappa semantica"
            body="Ogni punto è un intervento, posizionato per prossimità di significato. Evidenzia un tema o un gruppo per vedere dove si concentra il suo discorso."
          />
          <Feature
            icon={BarChart3}
            title="Analisi aggregate"
            body="Identità tematica, affinità e coesione tra gruppi, andamenti nel tempo, leggibilità e polarizzazione del linguaggio."
          />
          <Feature
            icon={Users}
            title="Profili individuali"
            body="Per ogni parlamentare: verbosità, ricchezza lessicale, costanza tematica, regolarità degli interventi e rete delle citazioni."
          />
        </div>
      </section>

      <section className="mt-14 border-t border-rule pt-10">
        <h2 className="text-h2">Come leggere la mappa</h2>
        <ol className="mt-5 max-w-3xl">
          {[
            'Scegli la fonte — Camera o Senato — e, se serve, restringi a un anno o a un mese.',
            'Passa da «interventi» a «deputati» per vedere i singoli discorsi oppure la posizione media di ciascun parlamentare.',
            'Evidenzia fino a tre temi o gruppi dalla legenda: il resto della mappa resta come contesto, in grigio.',
            'Clicca un punto per leggerne il testo e aprire il resoconto ufficiale della seduta.',
          ].map((text, i) => (
            <li
              key={text}
              className="flex gap-4 border-b border-rule py-3.5 last:border-b-0"
            >
              <span className="tabular shrink-0 text-num font-semibold text-muted">
                {String(i + 1).padStart(2, '0')}
              </span>
              <span className="text-body text-secondary">{text}</span>
            </li>
          ))}
        </ol>
      </section>

      <footer className="mt-14 flex flex-wrap items-center justify-between gap-4 border-t border-rule pt-6">
        <p className="max-w-xl text-label text-muted">
          I dati derivano dai resoconti stenografici pubblicati da camera.it e senato.it. Le
          metriche sono calcolate sul testo degli interventi, non sui voti.{' '}
          <Link to="/metodo" className="text-accent">
            Leggi la nota metodologica
          </Link>
          .
        </p>
        <a
          href="https://github.com/WeridFire/Parliament-Speech-Analyzer"
          target="_blank"
          rel="noreferrer noopener"
          className="inline-flex items-center gap-1.5 text-label text-muted no-underline hover:text-ink"
        >
          <Github size={14} aria-hidden="true" />
          CODICE SORGENTE
        </a>
      </footer>
    </Page>
  );
}

function Feature({ icon: Icon, title, body }) {
  return (
    <article className="bg-surface p-5">
      <Icon size={17} className="text-muted" aria-hidden="true" />
      <h3 className="mt-3 text-h3">{title}</h3>
      <p className="mt-1.5 text-body text-secondary">{body}</p>
    </article>
  );
}
