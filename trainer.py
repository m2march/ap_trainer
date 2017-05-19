# coding: utf-8
import music21 as m21
import sys
import time
import os
import glob
import random
import gflags
import re
from google.apputils import app
from subprocess import Popen, PIPE


DEFAULT_COLLECTIONS = ['ejemplos/ina2/*.tnc', 'ejemplos/a1/*.tnc']

gflags.DEFINE_integer('min_note_count', 2, 'Minimun note count per segment',
                      lower_bound=1, short_name='n')
gflags.DEFINE_integer('min_beat_count', 1, 'Minimun note count per segment',
                      lower_bound=1, short_name='b')
gflags.DEFINE_integer('segment_count', 1, 'Number of segments to test',
                      lower_bound=1, short_name='s')
gflags.DEFINE_integer('bpm', 80, 'Speed of segments. If None, use original',
                      lower_bound=60, upper_bound=200, short_name='m')
gflags.DEFINE_multistring('collections', DEFAULT_COLLECTIONS, 
                          'Collections to use')
gflags.DEFINE_bool('random_key', False, 'Whether to use a random key',
                   short_name='r')


FLAGS = gflags.FLAGS

KEY = m21.pitch.Pitch('C')

SCORE_FILE = 'score.csv'


class ABCParseException(ValueError):
    pass


def tiny_collection_parser(tiny_line):
    preamble, notes = tiny_line.split('|', 1)
    key_match = re.search('K:([A-G])', preamble)
    if key_match is not None:
        key_text = key_match.groups()[0]
    else:
        key_text = 'C'

    ts_match = re.search('TS:([0-9]*/[0-9])', preamble)
    if ts_match is not None:
        ts_text = ts_match.groups()[0]
    else:
        ts_text = '4/4'

    key = m21.key.Key(key_text)

    notes = notes.replace('|', '')
    tiny_notation = 'tinyNotation: ' + ts_text + ' ' + notes
    stream = m21.converter.parse(tiny_notation)
    stream = stream.flat
    stream.insert(0, key)
    return stream


def parse_abc(abc_file):
    s = m21.converter.parse(abc_file)
    mms = s.recurse().getElementsByClass('MetronomeMark')
    if len(mms) > 1:
        raise ABCParseException('%s has more then one MetronomeMark' % abc_file)

    tss = s.recurse().getElementsByClass('TimeSignature')
    if len(tss) > 1:
        raise ABCParseException('%s has more than one TimeSignature' % abc_file)

    keys = s.recurse().getElementsByClass('KeySignature')
    if len(keys) > 1:
        raise ABCParseException('% has more than one KeySignature' % abc_file)

    return s


def flat_and_in_c(s):
    tss = s.recurse().getElementsByClass('TimeSignature')
    ts = tss[0]

    keys = s.recurse().getElementsByClass('KeySignature')
    key = keys[0]

    new_notes = transpose_segment(s, key.asKey().tonic, KEY)

    return (ts, new_notes)


def transpose_segment(s, original_key, final_key):
    def transpose_note_or_rest(nr, interval):
        if isinstance(nr, m21.note.Note):
            return nr.transpose(interval)
        else:
            return nr

    interval = m21.interval.Interval(original_key, final_key)

    old_notes = s.flat.notesAndRests
    new_notes = [transpose_note_or_rest(n, interval) for n in old_notes]
    for on, nn in zip(old_notes, new_notes):
        nn.offset = on.offset

    return new_notes


def streams_from_tnc(tnc_filename):
    with open(tnc_filename, 'r') as f:
        streams = [tiny_collection_parser(l) for l in f]
    return streams


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

    ts, note_list = stream_info
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


def is_valid_ans(ans):
    pattern = '[a-gA-G\-][a-gA-G\-]*'
    return ans is not None and re.match(pattern, ans) is not None

def notes_from_ans(ans):
    notes = []
    note = None
    for x in ans:
        if x in list('abcdefg'):
            if note is not None:
                notes.append(note)
            note = x
        elif x == '-':
            note = note + x
    notes.append(note)
    return notes


def are_correct_notes(notes_string, segment):
    notes = notes_from_ans(notes_string)
    expected_notes = segment_notes(segment)
    correct_notes = [n.lower() == ex.lower()
                     for n, ex in zip(notes, expected_notes)].count(False)
    return correct_notes + abs(len(expected_notes) - len(notes))


def segment_notes(segment):
    return [n.pitch.name for n in segment if isinstance(n, m21.note.Note)]


def segment_from_segment_and_notes(original_segment, new_notes):
        tss = original_segment.recurse().getElementsByClass('TimeSignature')
        ts = tss[0]
        mms = original_segment.recurse().getElementsByClass('MetronomeMark')
        mm = mms[0]
        new_segment = m21.stream.Stream()
        new_segment.append([mm, ts])
        new_segment.append(new_notes)
        return new_segment


def play_segment(segment, key):
    if key.name != KEY.name:
        new_notes = transpose_segment(segment, KEY, key)
        transposed_segment = segment_from_segment_and_notes(segment, new_notes)
    else:
        transposed_segment = segment

    midifile = m21.midi.translate.streamToMidiFile(transposed_segment)
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
    stream.append(m21.meter.TimeSignature('4/4'))
    stream.append(m21.key.Key(pitch))
    for p in scale.pitches:
        stream.append(m21.note.Note(p, quarterLength=1.0))
    stream.append(m21.note.Rest(quarterLength=1.0))
    stream.append(m21.note.Note(scale.pitches[0], quarterLength=1.0))
    return stream


def comparison_segment(ans_text, expected_stream):
    ret_stream = m21.stream.Stream()
    ret_stream.append(expected_stream.getElementsByClass('MetronomeMark')[0])
    ret_stream.append(expected_stream.getElementsByClass('TimeSignature')[0])
    ret_stream.append(expected_stream.getElementsByClass('Key')[0])

    ans_notes_names = list(ans_text)
    ans_notes = []
    note_counter = 0
    for nr in expected_stream.notesAndRests:
        if isinstance(nr, m21.note.Rest):
            continue
        n = m21.note.Note(ans_notes_names[note_counter])
        n.octave = nr.octave
        n.duration = nr.duration
        ans_notes.append(n)
        note_counter += 1

    # TODO(march): finish


def record_score(note_accuracy, segment_accuracy, total_time, key):
    columns = ['min_note_count', 'min_beat_count', 'segment_count', 'bpm',
               'key', 'note_accuracy', 'segment_accuracy', 'total_time']
    f = None
    if not os.path.isfile(SCORE_FILE):
        f = open(SCORE_FILE, 'w')
        f.write('# ' + ', '.join(columns) + '\n')

    if f is None:
        f = open(SCORE_FILE, 'a')

    elems = [FLAGS.min_note_count, FLAGS.min_beat_count,
             FLAGS.segment_count, FLAGS.bpm,
             key.name if FLAGS.random_key else 'random',
             '{:.2f}'.format(note_accuracy),
             '{:.2f}'.format(segment_accuracy),
             '{:.2f}'.format(total_time)]
    f.write(', '.join([str(x) for x in elems]) + '\n')
    f.close()


def random_key():
    k = random.choice(['Ab3', 'A3', 'Bb3', 'B3', 'C4',
                       'C#4', 'D#4', 'E4', 'F4', 'F#4', 'G4'])
    return m21.pitch.Pitch(k)


def main(argv):
    key = KEY if not FLAGS.random_key else random_key()
    collections_files = [f
                         for tnc_glob in FLAGS.collections
                         for f in glob.glob(tnc_glob)]

    all_segments = [segment
                    for collections in collections_files
                    for stream in streams_from_tnc(collections)
                    for segment in extract_segments(
                        flat_and_in_c(stream),
                        FLAGS.min_note_count, FLAGS.min_beat_count)]

    segments = random.sample(all_segments, FLAGS.segment_count)

    scale = scale_from_pitch(key)
    print key
    play_segment(scale, key)

    total_note_count = 0.
    note_error_count = 0.
    segment_error_count = 0.
    repeat_counts = []
    try:
        start_time = time.time()
        for idx, segment in enumerate(segments):
            ans = None
            end_song = False
            repeat_count = 0
            while not end_song:
                repeat_count += 1
                play_segment(segment, key)
                ans = raw_input('> ')
                if not is_valid_ans(ans):
                    continue
                errors = are_correct_notes(ans, segment)
                total_note_count += len(segment.notes)
                if errors == 0:
                    sys.stdout.write(u' ✓\n')
                else:
                    note_error_count += errors
                    segment_error_count += 1
                    sys.stdout.write(u'✗ {}\n'.format(
                        ''.join(segment_notes(segment))))
                repeat_segment = segment
                repeat_counts.append(repeat_count)

                ask = True
                while ask:
                    sys.stdout.write('Next / repeat (n/r)? ')
                    ans = raw_input()
                    if ans.lower() == 'r':
                        play_segment(repeat_segment, key)
                    elif ans.lower() == 'n':
                        ask = False
                        end_song = True

        end_time = time.time()
        note_accuracy = (1 - (note_error_count / total_note_count))
        segment_accuracy = (1 - (segment_error_count / len(segments)))
        record_score(note_accuracy, segment_accuracy, end_time - start_time,
                     key)
        print 'Note accuracy: {:.0f}%'.format(100 * note_accuracy)
        print 'Segment accuracy: {:.0f}%'.format(100 * segment_accuracy)
    except KeyboardInterrupt:
        print ''
        pass


if __name__ == '__main__':
    app.run()
