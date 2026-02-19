'''
Author: Anthony Badea
Date: January 26, 2026
Purpose: Wrapper to run Analyze.cxx with config handled in Python
'''

import os
import argparse
import tempfile

# Global configuration for different file types
FILE_CONFIGS = {
    'LEP1Data': {
        'inFileType': 'LEP1Data',
        'treeNames': ['t']
    },
    'PYTHIA8': {
        'inFileType': 'PYTHIA8',
        'treeNames': ['tgenBefore']
    },
    'Herwig': {
        'inFileType': 'Herwig',
        'treeNames': ['tgenBefore']
    },
    'Sherpa': {
        'inFileType': 'Sherpa',
        'treeNames': ['tgenBefore']
    },
    'ALEPHMC': {  # Default
        'inFileType': 'ALEPHMC',
        'treeNames': ['t', 'tgen', 'tgenBefore']
    },
}

DEFAULT_SELECTION = {
    'nTPCcut': 4,
    'chargedTracksAbsCosThCut': 0.94,
    'ptCut': 0.2,  # GeV
    'd0Cut': 2,    # cm
    'z0Cut': 10,   # cm
    'ECut': 0.4,   # GeV
    'neutralTracksAbsCosThCut': 0.98,
    'TotalTrkEnergyCut': 15,   # GeV
    'AbsCosSThetaCut': 0.82,
    'NTrkCut': 5,
    'NeuNchCut': 13,
    'EVisCut': 0,     # GeV
    'MissPCut': 9999, # GeV
    'keepChargedTracks': True,
    'keepNeutralTracks': True,
    'doMET': False,
    'NES': -1, # neutral particle energy scale (NES) variation
    'NER': -1, # neutral particle efficiency variation via random throwing (NER)
}

REQUIRED_KEYS = set(DEFAULT_SELECTION.keys()) | {'inFileType', 'treeNames'}


def config_to_string(config):
    parts = []
    for key, value in config.items():
        if isinstance(value, bool):
            parts.append(f"{key}={'true' if value else 'false'}")
        elif isinstance(value, list):
            parts.append(f"{key}={','.join(map(str, value))}")
        else:
            parts.append(f"{key}={value}")
    return ";".join(parts)


def get_file_config(input_file):
    filename = os.path.basename(input_file)
    for file_type, config in FILE_CONFIGS.items():
        if file_type.lower() in filename.lower():
            return config.copy()
    print(f"Did not find file config for {filename}. Defaulting to PYTHIA8 config")
    return FILE_CONFIGS['PYTHIA8']


def validate_config(cfg):
    missing = REQUIRED_KEYS - set(cfg.keys())
    if missing:
        raise ValueError(f"Missing required config keys: {sorted(missing)}")


def create_selection_variations():
    variations = []

    # No event selections
    no_event_sel = DEFAULT_SELECTION.copy()
    no_event_sel.update({
        'TotalTrkEnergyCut': 0,
        'AbsCosSThetaCut': 1,
        'NTrkCut': 0,
        'NeuNchCut': 0,
        'EVisCut': 0
    })
    variations.append(('no_event_sel', no_event_sel))

    # Nominal selection
    variations.append(('nominal', DEFAULT_SELECTION.copy()))

    # nTPC variation: 4 -> 7
    ntpc7 = DEFAULT_SELECTION.copy()
    ntpc7['nTPCcut'] = 7
    variations.append(('ntpc7', ntpc7))

    # Charged tracks pT variation: 0.2 -> 0.4 GeV
    pt04 = DEFAULT_SELECTION.copy()
    pt04['ptCut'] = 0.4
    variations.append(('pt04', pt04))

    # Total charged energy variation: 15 -> 10 GeV
    ech10 = DEFAULT_SELECTION.copy()
    ech10['TotalTrkEnergyCut'] = 10
    variations.append(('ech10', ech10))

    # Thrust without neutral objects
    no_neutrals = DEFAULT_SELECTION.copy()
    no_neutrals['keepNeutralTracks'] = False
    variations.append(('no_neutrals', no_neutrals))

    # Thrust with missing momentum vector
    with_met = DEFAULT_SELECTION.copy()
    with_met['doMET'] = True
    variations.append(('with_met', with_met))

    # vary neutral particle energy scale up
    nes_up = DEFAULT_SELECTION.copy()
    nes_up['NES'] = 1.05
    variations.append(('nes_up', nes_up))

    # vary neutral particle energy scale down
    nes_down = DEFAULT_SELECTION.copy()
    nes_down['NES'] = 0.95
    variations.append(('nes_down', nes_down))

    # vary neutral particle efficiency by randomly throwing away with probability x%
    ner = DEFAULT_SELECTION.copy()
    ner['NER'] = 0.025
    variations.append(('ner', ner))

    return variations


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('-i', '--input', required=True, help='Input ROOT file')
    p.add_argument('-o', '--output', default='', help='Output ROOT file (only if single job)')
    p.add_argument('--outDir', default='./', help='Output directory (default: ./)')
    p.add_argument('-t', '--tree', default='', help='Override tree name (single tree)')
    p.add_argument('--file-type', default='', help='Override inFileType')
    p.add_argument('-n', '--nevents', type=int, default=-1, help='Number of events to process')
    p.add_argument('-j', '--threads', type=int, default=0, help='Number of threads for ImplicitMT')
    p.add_argument('--debug', action='store_true', help='Disable ImplicitMT and enable debug prints')
    p.add_argument('--config-out', default='', help='Write config to this path (single job only)')
    p.add_argument('--nominalOnly', action='store_true', help='Only run the nominal selection variation')
    p.add_argument('--nesOnly', action='store_true', help='Only run the neutral particle energy scale selection variation')
    p.add_argument('--onlyThese', nargs='+', help='List of variation names to run (space-separated)')
    p.add_argument('--dryrun', action='store_true', help='Print commands without executing them')
    return p.parse_args()


def run_analyze_job(job_config):
    cmd_parts = [
        './bin/Analyze.exe',
        f"-i {job_config['input_file']}",
        f"-o {job_config['output_file']}",
        f"-C {job_config['config_path']}"
    ]
    if job_config['nevents'] != -1:
        cmd_parts.append(f"-n {job_config['nevents']}")
    if job_config['threads'] > 0:
        cmd_parts.append(f"-j {job_config['threads']}")
    if job_config['debug']:
        cmd_parts.append('--debug')

    cmd = ' '.join(cmd_parts)
    print(f"[{job_config['selection_name']}] {cmd}")
    if not job_config['dryrun']:
        rc = os.system(cmd)
    else:
        rc = 0
    if job_config.get('temp_config') and os.path.exists(job_config['config_path']):
        os.remove(job_config['config_path'])
    return rc


def main():
    ops = parse_args()
    os.makedirs(ops.outDir, exist_ok=True)

    file_cfg = get_file_config(ops.input)
    if ops.file_type:
        file_cfg['inFileType'] = ops.file_type
    if ops.tree:
        file_cfg['treeNames'] = [ops.tree]

    variations = create_selection_variations()

    if ops.nominalOnly:
        variations = [variations[1]]

    if ops.nesOnly:
        variations = [i for i in variations if i[0] in ['nominal', 'nes_up', 'nes_down', 'no_neutrals']]

    if ops.onlyThese:
        variations = [i for i in variations if i[0] in ops.onlyThese]

    tree_names = file_cfg['treeNames']
    total_trees = len(tree_names)
    print(f"Running {len(variations)} selection variations with {total_trees} trees each")

    base = os.path.splitext(os.path.basename(ops.input))[0]

    job_configs = []
    for sel_name, selection in variations:
        for tree_name in tree_names:
            if tree_name in ['tgen', 'tgenBefore'] and sel_name != 'no_event_sel':
                print(f"[{sel_name}] Skipping tree: {tree_name} (generator-level trees only run with no_event_sel)")
                continue

            tree_config = {
                'inFileType': file_cfg['inFileType'],
                'treeNames': tree_name
            }
            combined = {}
            combined.update(tree_config)
            combined.update(selection)
            validate_config(combined)

            config_str = config_to_string(combined)

            if ops.config_out and total_trees == 1 and len(variations) == 1:
                cfg_path = ops.config_out
                with open(cfg_path, 'w') as f:
                    f.write(config_str)
                temp_config = False
            else:
                fd, cfg_path = tempfile.mkstemp(prefix='analyze_cfg_', suffix='.txt')
                with os.fdopen(fd, 'w') as f:
                    f.write(config_str)
                temp_config = True

            if ops.output and total_trees == 1 and len(variations) == 1:
                out_file = ops.output
            else:
                out_file = os.path.join(ops.outDir, f"{base}_thrust_{sel_name}_{tree_name}.root")

            job_configs.append({
                'input_file': ops.input,
                'output_file': out_file,
                'config_path': cfg_path,
                'selection_name': f"{sel_name}_{tree_name}",
                'nevents': ops.nevents,
                'threads': ops.threads,
                'debug': ops.debug,
                'dryrun': ops.dryrun,
                'temp_config': temp_config
            })

    failures = []
    for job in job_configs:
        rc = run_analyze_job(job)
        if rc != 0:
            failures.append((job['selection_name'], rc))

    if failures:
        print("One or more Analyze jobs failed:")
        for sel_name, rc in failures:
            print(f"  {sel_name}: exit {rc}")
        raise SystemExit(1)


if __name__ == '__main__':
    main()
