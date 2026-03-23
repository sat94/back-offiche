import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'back_office.settings'

import django
django.setup()

from django.conf import settings

MONITORING_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_prometheus_config():
    targets = settings.MONITORING_TARGETS
    scrape_configs = []
    for key, info in targets.items():
        scrape_configs.append({
            'job_name': key,
            'static_configs': [{'targets': [f'host.docker.internal:{info["local_port"]}'], 'labels': {'server': info['label']}}],
            'scrape_interval': '15s',
        })

    config = {
        'global': {'scrape_interval': '15s', 'evaluation_interval': '15s'},
        'scrape_configs': scrape_configs,
    }

    import yaml
    config_path = os.path.join(MONITORING_DIR, 'prometheus.yml')
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    print(f"Prometheus config written to {config_path}")
    for key, info in targets.items():
        print(f"  {info['label']}: localhost:{info['local_port']}")


def generate_grafana_dashboard():
    panels = []
    targets_list = list(settings.MONITORING_TARGETS.items())

    panel_defs = [
        ('CPU Usage %', 'percent', '100 - (avg by(instance)(irate(node_cpu_seconds_total{{mode="idle",job="{job}"}}[5m])) * 100)'),
        ('Memory Usage %', 'percent', '(1 - node_memory_MemAvailable_bytes{{job="{job}"}} / node_memory_MemTotal_bytes{{job="{job}"}}) * 100'),
        ('Disk Usage %', 'percent', '(1 - node_filesystem_avail_bytes{{job="{job}",mountpoint="/"}} / node_filesystem_size_bytes{{job="{job}",mountpoint="/"}}) * 100'),
        ('Network In (bytes/s)', 'Bps', 'irate(node_network_receive_bytes_total{{job="{job}",device!~"lo|veth.*|docker.*|br-.*"}}[5m])'),
        ('Network Out (bytes/s)', 'Bps', 'irate(node_network_transmit_bytes_total{{job="{job}",device!~"lo|veth.*|docker.*|br-.*"}}[5m])'),
        ('Load Average (1m)', 'short', 'node_load1{{job="{job}"}}'),
    ]

    panel_id = 1
    for row_idx, (key, info) in enumerate(targets_list):
        panels.append({
            'id': panel_id,
            'type': 'row',
            'title': info['label'],
            'gridPos': {'h': 1, 'w': 24, 'x': 0, 'y': row_idx * 9},
            'collapsed': False,
        })
        panel_id += 1

        for col_idx, (title, unit, expr_tpl) in enumerate(panel_defs):
            expr = expr_tpl.format(job=key)
            x = (col_idx % 4) * 6
            y = row_idx * 9 + 1 + (col_idx // 4) * 4
            panels.append({
                'id': panel_id,
                'type': 'timeseries',
                'title': title,
                'gridPos': {'h': 4, 'w': 6, 'x': x, 'y': y},
                'datasource': {'type': 'prometheus', 'uid': 'PBFA97CFB590B2093'},
                'targets': [{'expr': expr, 'legendFormat': '{{instance}}', 'refId': 'A'}],
                'fieldConfig': {
                    'defaults': {
                        'unit': unit,
                        'thresholds': {'mode': 'absolute', 'steps': [
                            {'color': 'green', 'value': None},
                            {'color': 'yellow', 'value': 70},
                            {'color': 'red', 'value': 90},
                        ]},
                    },
                    'overrides': [],
                },
                'options': {'tooltip': {'mode': 'single'}, 'legend': {'displayMode': 'hidden'}},
            })
            panel_id += 1

    dashboard = {
        'dashboard': {
            'id': None,
            'uid': 'meetvoice-servers',
            'title': 'MeetVoice - Serveurs',
            'tags': ['meetvoice'],
            'timezone': 'Europe/Paris',
            'refresh': '30s',
            'time': {'from': 'now-1h', 'to': 'now'},
            'panels': panels,
            'schemaVersion': 39,
            'version': 1,
        },
    }

    dashboards_dir = os.path.join(MONITORING_DIR, 'dashboards')
    os.makedirs(dashboards_dir, exist_ok=True)
    dashboard_path = os.path.join(dashboards_dir, 'servers.json')
    with open(dashboard_path, 'w') as f:
        json.dump(dashboard['dashboard'], f, indent=2)
    print(f"Grafana dashboard written to {dashboard_path}")


def start_docker():
    subprocess.run(['docker', 'compose', 'up', '-d'], cwd=MONITORING_DIR, check=True)
    print("\nPrometheus: http://localhost:9090")
    print("Grafana:    http://localhost:3000  (admin / meetvoice2025)")


if __name__ == '__main__':
    try:
        import yaml
    except ImportError:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyyaml'], check=True)
        import yaml

    generate_prometheus_config()
    generate_grafana_dashboard()
    start_docker()
