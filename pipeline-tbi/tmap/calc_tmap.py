# -*- coding: utf-8 -*-

import os
import sys
import mne
import numpy as np

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_PATH)

from visualize.visualize import visualize_stc
from averages.get_avg import get_cohorts

type = 'random'

def calc_tmap(stc_fpath, avg_stc_fpath, var_stc_fpath, outfile):
    sub_stc = mne.read_source_estimate(stc_fpath, 'fsaverage')
    avg_stc = mne.read_source_estimate(avg_stc_fpath, 'fsaverage')
    var_stc = mne.read_source_estimate(var_stc_fpath, 'fsaverage')
    sd = np.sqrt(var_stc.data)

    t_data = (sub_stc.data - avg_stc.data) / sd
    tmap_stc = sub_stc.copy()
    tmap_stc.data = t_data

    tmap_stc.save(outfile)

    data_outfile = outfile + '-data.csv'
    np.savetxt(data_outfile, t_data, fmt='%.5f', delimiter=",")

    return tmap_stc


def plot_tmap(tmap_stc_fname, subject, fig_fname, subjects_dir):
    visualize_stc(tmap_stc_fname, fig_fname, subjects_dir, subject, colormap='coolwarm', clim=dict(kind='value', pos_lims=[0.0, 1.0, 2.0]))


def main(subject, task, data_dir, subjects_dir, averages_dir, cohorts=True, window=True):
    if cohorts:
        raw_fname = os.path.join(data_dir, subject, 'ica', f'{subject}-{task}-ica-recon.fif')
        raw = mne.io.Raw(raw_fname)
        birthyear = raw.info['subject_info']['birthday'][0]
        meas_year = raw.info['meas_date'].year
        age = meas_year - birthyear
        cohort_idx = int((age - 8) / 10)
        print('Cohort:', cohort_idx)
        avg_stc_fpath = os.path.join(averages_dir, f'cohort-{cohort_idx}-camcan-avg-{type}')
        var_stc_fpath = os.path.join(averages_dir, f'cohort-{cohort_idx}-camcan-var-{type}')
    else:
        avg_stc_fpath = os.path.join(averages_dir, f'camcan-avg-{type}')
        var_stc_fpath = os.path.join(averages_dir, f'camcan-var-{type}')

    outdir = os.path.join(data_dir, subject, 'tmap')
    os.makedirs(outdir, exist_ok=True)

    if window:
        for i in range(40, 390, 50):
            stc_fpath = os.path.join(data_dir, subject, 'psd', f'{subject}-{task}-{i}-psd-fsaverage')
            if cohorts:
                tmap_outfile = os.path.join(outdir, f'{subject}-{task}-{i}-{type}-cohort-psd-tmap')
                fig_fpath = os.path.join(data_dir, subject, 'fig', f'{subject}-{task}-{i}-{type}-cohort-psd-tmap.png')
            else:
                tmap_outfile = os.path.join(outdir, f'{subject}-{task}-{i}-{type}-psd-tmap')
                fig_fpath = os.path.join(data_dir, subject, 'fig', f'{subject}-{task}-{i}-{type}-psd-tmap.png')
            tmap = calc_tmap(stc_fpath, avg_stc_fpath, var_stc_fpath, tmap_outfile)
            plot_tmap(tmap_outfile, subject, fig_fpath, subjects_dir)
    else:
        stc_fpath = os.path.join(data_dir, subject, 'psd', f'{subject}-{task}-full-psd-fsaverage')
        if cohorts:
            tmap_outfile = os.path.join(outdir, f'{subject}-{task}-{type}-cohort-psd-tmap')
            fig_fpath = os.path.join(data_dir, subject, 'fig', f'{subject}-{task}-{type}-cohort-psd-tmap.png')
        else:
            tmap_outfile = os.path.join(outdir, f'{subject}-{task}-{type}-psd-tmap')
            fig_fpath = os.path.join(data_dir, subject, 'fig', f'{subject}-{task}-{type}-psd-tmap.png')
        tmap = calc_tmap(stc_fpath, avg_stc_fpath, var_stc_fpath, tmap_outfile)
        plot_tmap(tmap_outfile, subject, fig_fpath, subjects_dir)


if __name__ == '__main__':
    main(*sys.argv[1:])

