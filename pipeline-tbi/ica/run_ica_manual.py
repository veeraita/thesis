# -*- coding: utf-8 -*-

import os
import sys
import argparse
import mne
import matplotlib.pyplot as plt
from mne.preprocessing import read_ica
from run_ica import fit_ica, get_excludes, plot_ica_results, create_report


def run_ica_manual(subj, task, raw_fname, output_dir, fit=False, all_manual=False):
    ica_dir = os.path.join(output_dir, subj, 'ica')
    os.makedirs(ica_dir, exist_ok=True)

    raw = mne.io.Raw(raw_fname)
    ica_fname = os.path.join(ica_dir, f'{subj}-{task}-ica.fif')
    if fit:
        # fit with more components
        ica = fit_ica(raw.copy(), decim=3, n_components=0.92, reject=dict(mag=5e-12, grad=5000e-13))
        ecg_inds, ecg_scores, eog_inds, eog_scores = get_excludes(ica, raw)
        ica.labels_['ecg'] = ecg_inds
        ica.labels_['eog'] = eog_inds
    else:
        ica = read_ica(ica_fname)
        ecg_inds = ica.labels_.get('ecg', [])
        eog_inds = ica.labels_.get('eog', [])
        if len(ecg_inds) > 0 and (len(eog_inds) > 0 or task != 'EO') and not all_manual:
            print("Nothing to be done for subject", subj)
            return

    print(ica.labels_)

    ecg_channel_picks = mne.pick_types(raw.info, meg=False, ecg=True)
    if len(ecg_channel_picks) > 0:
        ecg_channel = raw.info['ch_names'][ecg_channel_picks[0]]
        ecg_scores = ica.score_sources(raw, ecg_channel)
    else:
        ecg_scores = None

    eog_channel_picks = mne.pick_types(raw.info, meg=False, eog=True)
    if len(eog_channel_picks) > 0:
        eog_channel = raw.info['ch_names'][eog_channel_picks[0]]
        eog_scores = ica.score_sources(raw, eog_channel)
    else:
        eog_scores = None

    print("ECG ICs found automatically:", ecg_inds)
    print("EOG ICs found automatically:", eog_inds)

    if (len(ecg_inds) == 0) or all_manual:
        ica.exclude = ecg_inds
        ica.plot_sources(raw, title="Mark the ICs corresponding to ECG artifacts")
        plt.show()
        new_ecg_inds = ica.exclude
        print("ECG ICs found by manual inspection:", new_ecg_inds)
        ica.labels_['ecg/manual'] = new_ecg_inds
        ica.labels_['ecg'] = new_ecg_inds
    else:
        new_ecg_inds = ecg_inds

    if (len(eog_inds) == 0) or all_manual:
        ica.exclude = eog_inds
        ica.plot_sources(raw, title="Mark the ICs corresponding to EOG artifacts")
        plt.show()
        new_eog_inds = ica.exclude
        print("EOG ICs found by manual inspection:", new_eog_inds)
        ica.labels_['eog/manual'] = new_eog_inds
        ica.labels_['eog'] = new_eog_inds
    else:
        new_eog_inds = eog_inds

    #new_ecg_inds = ecg_inds
    #new_eog_inds = eog_inds

    n_max_ecg, n_max_eog = 2, 2

    if new_ecg_inds is not None and len(new_ecg_inds) > n_max_ecg and not all_manual:
        new_ecg_inds = new_ecg_inds[:n_max_ecg]
    if new_eog_inds is not None and len(new_eog_inds) > n_max_eog and not all_manual:
        new_eog_inds = new_eog_inds[:n_max_eog]

    if (new_ecg_inds != ecg_inds) or (new_eog_inds != eog_inds) or fit:
        report_fname = os.path.join(ica_dir, f'{subj}-{task}-ica-report.html')
        figs, captions = plot_ica_results(ica, raw, new_ecg_inds, ecg_scores, new_eog_inds, eog_scores)
        create_report(subj, task, raw_fname, report_fname, figs, captions)

        print(ica.labels_)
        ica.exclude = new_ecg_inds + new_eog_inds
        out_fname = os.path.join(ica_dir, f'{subj}-{task}-ica.fif')
        ica.save(out_fname)


def main():
    input_dir = os.environ['INPUT_DIR']
    output_dir = os.environ['OUTPUT_DIR']

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file', help='Path to a file containing pairs of (subject, task) to process', default=None)
    parser.add_argument('--fit', help='Re-fit ICA', action='store_true', default=False)
    parser.add_argument('--all-manual', help='Select components manually even if some are found automatically',
                        action='store_true', default=False)
    parser.add_argument('--task', help='The task(s) to process. Ignored if --file is used', nargs='*', default=None)
    parser.add_argument('subject', help='The subject to process', nargs='?', default=None)
    args = parser.parse_args()

    if not args.file and not args.subject:
        parser.error('Subject ID is required if --file option is not set')

    if args.file:
        # read a list of subjects and tasks from file
        if not os.path.isfile(args.file):
            raise FileNotFoundError('The given file does not exist')

        with open(args.file) as f:
            failed_cases = f.readlines()
        # get list of tuples (subject, task)
        failed_cases = [x.strip().split()[:2] for x in failed_cases]

    else:
        if not args.task:
            if 'camcan' in input_dir:
                tasks = ['rest']
            else:
                tasks = ['EO', 'EC']
        else:
            tasks = args.task
        failed_cases = [(args.subject, task) for task in tasks]

    checked_file = os.path.join(output_dir, 'checked.txt')
    for subject, task in failed_cases:
        if 'camcan' in input_dir:
            raw_fname = os.path.join(input_dir, subject, 'meg', f'{task}_raw_tsss_mc.fif')
        else:
            raw_fname = os.path.join(input_dir, f'{subject}_{task}_tsss_mc.fif')
        try:
            print(subject, task)
            run_ica_manual(subject, task, raw_fname, output_dir, fit=args.fit, all_manual=args.all_manual)
            # write manually checked cases to file
            with open(checked_file, 'a+') as f:
                f.write(subject + ' ' + task + '\n')
        except Exception as e:
            print(e)
            print("Error while running ICA for subject", subject)


if __name__ == "__main__":
    main()
