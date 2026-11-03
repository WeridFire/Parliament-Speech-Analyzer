import { useMemo } from 'react';
import { Card, CardBody, CardFooter, CardHeader, RankingList, ScopeNote } from '../../ui';
import { useAnalysis } from './context';
import { partyDot, partyName, partyShort } from '../../domain/parties';
import { cleanName } from '../../data/selectors';
import { dec } from '../../lib/format';
import { NoDataForPeriod } from '../../ui/EmptyState';

/**
 * Readability and "us vs them" polarization of the phrasing.
 *
 * The lexicon sentiment that used to lead this tab is gone: 25 positive and 25
 * negative words ("problema", "rischio", "obiettivo"…) decided the tone of a
 * speech, topic averages were indistinguishable from zero, and the rankings
 * were led by members with a single speech scored +1.
 */
export default function Language() {
  const { section, period, mode } = useAnalysis();
  const { data: language, fromGlobal } = section('language');

  const readabilityRows = useMemo(
    () =>
      Object.entries(language?.readability?.by_party ?? {})
        .map(([party, info]) => ({
          key: party,
          name: partyName(party),
          meta: `${info.n_speeches} interventi`,
          percent: info.avg_score,
          value: dec(info.avg_score),
          tone: info.avg_score >= 80 ? 'good' : info.avg_score >= 55 ? 'warning' : 'critical',
          dot: partyDot(party, mode),
        }))
        .sort((a, b) => b.percent - a.percent),
    [language, mode],
  );

  const polarization = language?.polarization;

  const partyPolarization = useMemo(
    () =>
      Object.entries(polarization?.by_party ?? {})
        .map(([party, info]) => ({
          key: party,
          name: partyName(party),
          meta: `${info.n} interventi`,
          percent: info.pct,
          value: dec(info.raw),
          tone: 'critical',
          dot: partyDot(party, mode),
        }))
        .sort((a, b) => b.percent - a.percent),
    [polarization, mode],
  );

  /**
   * The bar shows the percentile — a claim the data supports ("more
   * oppositional phrasing than N% of colleagues") — while the printed value is
   * the raw rate in its actual unit.
   */
  const toRows = (list, tone) =>
    (list ?? []).map((p) => ({
      key: `${p.speaker}-${p.party}`,
      name: cleanName(p.speaker),
      meta: `${partyShort(p.party)} · ${p.n ?? 0} interventi`,
      percent: p.pct,
      value: dec(p.raw),
      tone,
      dot: partyDot(p.party, mode),
    }));

  if (!language) return <NoDataForPeriod feature="l'analisi del linguaggio" period={period} />;

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <div className="lg:col-span-2">
        <ScopeNote fromGlobal={fromGlobal} period={period} />
      </div>

      <Card>
        <CardHeader title="Leggibilità" subtitle="Indice Gulpease per gruppo: sotto 55 il testo è difficile" />
        <CardBody>
          <RankingList items={readabilityRows} />
        </CardBody>
        <CardFooter>
          LE FRASI SONO QUELLE DEL RESOCONTO STENOGRAFICO: LA PUNTEGGIATURA È DEGLI STENOGRAFI, NON
          DI CHI PARLA. LE DIFFERENZE FRA GRUPPI SONO PICCOLE E VANNO LETTE COME TALI.
        </CardFooter>
      </Card>

      <Card>
        <CardHeader title="Polarizzazione per gruppo" subtitle="Contrapposizioni «noi/loro» ogni mille parole" />
        <CardBody>
          <RankingList items={partyPolarization} />
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Linguaggio più polarizzato" subtitle="Parlamentari con almeno 10 interventi" />
        <CardBody>
          <RankingList items={toRows(polarization?.top_polarizers, 'critical')} />
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Linguaggio meno polarizzato" subtitle="Parlamentari con almeno 10 interventi" />
        <CardBody>
          <RankingList items={toRows(polarization?.least_polarizers, 'good')} />
        </CardBody>
        <CardFooter>
          LA BARRA INDICA LA POSIZIONE RELATIVA RISPETTO AGLI ALTRI PARLAMENTARI; IL VALORE È LA
          FREQUENZA DEI MARCATORI OGNI MILLE PAROLE. RIGUARDA LA FORMA DEL LINGUAGGIO, NON IL
          CONTENUTO DELLE POSIZIONI.
        </CardFooter>
      </Card>
    </div>
  );
}
