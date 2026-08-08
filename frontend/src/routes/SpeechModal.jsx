import { ExternalLink } from 'lucide-react';
import { Modal, PartyChip } from '../ui';
import { dateLabel } from '../lib/format';
import { cleanName } from '../data/selectors';
import { useTheme } from '../lib/useTheme';

/**
 * A single intervention.
 *
 * `text` is the original-case speech as delivered. It is truncated for the
 * payload, so the link to the official report is the way to read the whole
 * thing.
 */
export function SpeechModal({ speech, clusters, onClose }) {
  const { mode } = useTheme();
  if (!speech) return null;

  const body = speech.text || '';
  const topic = speech.cluster_label ?? clusters?.[speech.cluster]?.label;

  return (
    <Modal
      open
      onClose={onClose}
      size="lg"
      title={cleanName(speech.deputy)}
      subtitle={dateLabel(speech.date)}
      footer={
        speech.url ? (
          <a
            href={speech.url}
            target="_blank"
            rel="noreferrer noopener"
            className="inline-flex items-center gap-1.5 text-body no-underline hover:underline"
          >
            Resoconto stenografico della seduta
            <ExternalLink size={13} aria-hidden="true" />
          </a>
        ) : (
          <span className="text-label text-muted">Nessun collegamento disponibile.</span>
        )
      }
    >
      <div className="flex flex-wrap items-center gap-2">
        <PartyChip party={speech.party} mode={mode} short={false} size="sm" />
        {topic ? <span className="text-label text-muted">{topic.toUpperCase()}</span> : null}
      </div>

      <blockquote className="mt-5 border-l-2 border-rule pl-4 font-serif text-[1.0625rem] leading-[1.7] text-ink">
        {body}
      </blockquote>

      <p className="mt-5 text-label text-muted">
        Testo tratto dal resoconto stenografico. Le annotazioni d&apos;aula (applausi,
        interruzioni) sono state rimosse in fase di elaborazione.
      </p>
    </Modal>
  );
}
