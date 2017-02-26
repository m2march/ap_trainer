# coding: utf-8
import music21 as m21
import sys
import os
import glob
import random
import gflags
from google.apputils import app
from subprocess import Popen, PIPE


gflags.DEFINE_integer('min_note_count', 2, 'Minimun note count per segment',
                      lower_bound=1, short_name='n')
gflags.DEFINE_integer('min_beat_count', 1, 'Minimun note count per segment',
                      lower_bound=1, short_name='b')
gflags.DEFINE_integer('segment_count', 1, 'Number of segments to test',
                      lower_bound=1, short_name='s')
gflags.DEFINE_integer('bpm', None, 'Speed of segments. If None, use original',
                      lower_bound=60, upper_bound=200, short_name='m')


FLAGS = gflags.FLAGS

ABC_GLOB = 'ejemplos/*.abc'

ejemplos = glob.glob(ABC_GLOB)

KEY = m21.pitch.Pitch('C')


class ABCParseException(ValueError):
    pass


def flat_and_transposed(abc_file):
    s = m21.converter.parse(abc_file)
    mms = s.recurse().getElementsByClass('MetronomeMark')
    if len(mms) > 1:
        raise ABCParseException('%s has more then one MetronomeMark' % abc_file)
    mm = mms[0]

    tss = s.recurse().getElementsByClass('TimeSignature')
    if len(tss) > 1:
        raise ABCParseException('%s has more than one TimeSignature' % abc_file)
    ts = tss[0]

    keys = s.recurse().getElementsByClass('KeySignature')
    if len(keys) > 1:
        raise ABCParseException('% has more than one KeySignature' % abc_file)
    key = keys[0]

    interval = m21.interval.Interval(key.asKey().tonic, KEY)

    old_notes = s.flat.notesAndRests
    new_notes = [n.transpose(interval) for n in old_notes]
    for on, nn in zip(old_notes, new_notes):
        nn.offset = on.offset

    return (mm, ts, new_notes)


def extract_segments(stream_info, min_notes_count, min_beat_duration):
    '''
    Args:
        stream_info :: (MetrnomeMark, TimeSignature, [Note])
    '''
    def next_segment(notes_iterator):
        segment = []
        note_count = 0
        beat_count = 0
        last_note = None
        while (note_count < min_notes_count or
               beat_count < min_beat_duration or
               last_note is None or
               (last_note.offset + last_note.quarterLength) % 1 != 0):
            last_note = notes_iterator.next()
            segment.append(last_note)
            note_count += 1
            if (last_note.offset + last_note.quarterLength) % 1 == 0:
                beat_count += 1
        return segment

    mm, ts, note_list = stream_info
    if FLAGS.bpm is not None:
        mm = m21.tempo.MetronomeMark(number=FLAGS.bpm)

    notes_iterator = iter(note_list)
    keep_extract = True
    while keep_extract:
        try:
            segment = next_segment(notes_iterator)
            stream = m21.stream.Stream([mm, ts])
            stream.append(segment)
            yield stream
        except StopIteration:
            keep_extract = False


def are_correct_notes(notes_string, segment):
    notes = list(notes_string)
    expected_notes = segment_notes(segment)
    return [n.lower() == ex.lower()
            for n, ex in zip(notes, expected_notes)].count(False)


def segment_notes(segment):
    return [n.pitch.name for n in segment if isinstance(n, m21.note.Note)]


def play_segment(segment):
    midifile = m21.midi.translate.streamToMidiFile(segment)
    midifile.open('temp.mid', 'wb')
    midifile.write()
    midifile.close()
    proc = Popen(['timidity', 'temp.mid'], stdout=PIPE)
    proc.communicate()
    os.remove('temp.mid')


def scale_from_pitch(pitch):
    scale = m21.scale.DiatonicScale(pitch)
    stream = m21.stream.Stream()
    stream.append(m21.tempo.MetronomeMark(number=80))
    for p in scale.pitches:
        stream.append(m21.note.Note(p, quarterLength=1.0))
    stream.append(m21.note.Note(scale.pitches[0], quarterLength=4.0))
    return stream


def main(argv):
    all_segments = [segment
                    for example in glob.glob(ABC_GLOB)
                    for segment in extract_segments(
                        flat_and_transposed(example),
                        FLAGS.min_note_count, FLAGS.min_beat_count)]

    segments = random.sample(all_segments, FLAGS.segment_count)

    scale = scale_from_pitch(KEY)
    play_segment(scale)

    total_note_count = 0.
    note_error_count = 0.
    segment_error_count = 0.
    try:
        for idx, segment in enumerate(segments):
            play_segment(segment)
            sys.stdout.write('> ')
            ans = raw_input()
            errors = are_correct_notes(ans, segment)
            total_note_count += len(segment.notes)
            if errors == 0:
                sys.stdout.write(u' ✓\n')
            else:
                note_error_count += errors
                segment_error_count += 1
                sys.stdout.write(u' ✗ {}\n'.format(
                    ''.join(segment_notes(segment))))

            if idx < len(segments) - 1:
                sys.stdout.write('Next?')
                raw_input()

        note_accuracy = 100 * (1 - (note_error_count / total_note_count))
        segment_accuracy = 100 * (1 - (segment_error_count / len(segments)))
        print 'Note accuracy: {:.0f}%'.format(note_accuracy)
        print 'Segment accuracy: {:.0f}%'.format(segment_accuracy)
    except KeyboardInterrupt:
        print ''
        pass


if __name__ == '__main__':
    app.run()
