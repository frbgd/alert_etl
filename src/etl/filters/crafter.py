import datetime
import re
from typing import Optional, List

import pytz

from objects.etl_data import Alert
from settings import config


MILLISECONDS_IN_SECONDS = 1000


def craft_links(
        information_system: Optional[str] = None,
        use_case: Optional[str] = None,
        qradar_offense_id: Optional[str] = None,
        playbook_links: Optional[str] = None
) -> str:
    links_map = []
    if information_system:
        links_map.append(('RT SM Portal', config.link_smp_is.replace('{id}', information_system)))
    if use_case:
        links_map.append(('RT Use-Case Portal', config.link_ucp_uc.replace('{id}', use_case)))
    if qradar_offense_id:
        links_map.append(('QRadar link from VDI', config.link_qradar_from_vdi.replace('{id}', qradar_offense_id)))
        links_map.append(('QRadar link from KSPD', config.link_qradar_from_kspd.replace('{id}', qradar_offense_id)))
    if playbook_links:
        links_map.append(('Playbook Link', playbook_links))

    if not links_map:
        return ''

    links_str = '\n\n '.join([f'**{item[0]}:** {item[1]}' for item in links_map])
    return f'## Links\n\n {links_str}'


def craft_alert(alert: Alert) -> dict:
    return {
        'sourceRef': alert.source_ref,
        'title': {alert.use_case_title},
        'type': alert.use_case,
        'caseTemplate': alert.use_case,
        'source': alert.source,
        'severity': config.priority_to_severity_map.get(alert.priority, 3),
        'tags': [alert.source, alert.use_case, alert.use_case_status.name, alert.incident_category,
                 alert.information_system_status.name, alert.priority, alert.information_system],
        'artifacts': [],
        'customFields': {
            'resolutionCategory': {
                'string': 'None'
            },
            'resolutionSource': {
                'string': 'None'
            },
            'informationSystems': {
                'string': alert.information_system
            },
            'alertTime': {
                'date': int(datetime.datetime.now().timestamp() * MILLISECONDS_IN_SECONDS)
            },
            'incidentcategory': {
                'string': alert.incident_category
            },
            'incidentSource': {
                'string': alert.source
            },
            'UseCaseStatus': {
                'string': alert.use_case_status.name
            },
            'pendingReason': {
                'string': ''
            },
            'offenseType': {
                'string': alert.use_case
            },
            'priority': {
                'string': alert.priority
            },
            'observablesCount': {
                'integer': 0
            },
            'platformIncidentID': {
                'string': alert.source_ref
            }
        }
    }


def craft_elk_alert(alert: Alert):
    links = craft_links(
        information_system=alert.information_system,
        use_case=alert.use_case,
        playbook_links=alert.playbook_links
    )
    alert.data = craft_alert(alert)
    alert.data['title'] = f'{alert.use_case_title} ' \
                          f'({alert.raw_data.get("_source", {}).get("case.keyfield", "")} ' \
                          f'{alert.raw_data.get("_source", {}).get("target.ports", "")})'
    alert.data['description'] = f"{alert.raw_data.get('_source', {}).get('case.description', '')}\n\n{links}"
    alert.data['customFields']['externalSource'] = {
        'string': alert.raw_data.get('_source', {}).get('case.information.source', '')
    }
    alert.data['customFields']['elasticIndex'] = {
        'string': alert.raw_data.get('_source', {}).get('index.name', '')
    }
    alert.data['customFields']['keyField'] = {
        'string': alert.raw_data.get("_source", {}).get("case.keyfield", "") + ' ' +
                  alert.raw_data.get("_source", {}).get("target.ports", "")
    }

    detect_time = alert.raw_data.get('_source', {}).get('timestamp')
    if detect_time:
        res = re.findall(r'\d{4}-\d{2}-\d{2}T\d{2}\:\d{2}\:\d{2}\.\d{3}', detect_time)
        dt = datetime.datetime.strptime(res[0], '%Y-%m-%dT%H:%M:%S.%f')
        timezone = pytz.timezone("UTC")
        dt = timezone.localize(dt)
        alert.data['customFields']['detectTime'] = {
            'date': int(dt.timestamp() * MILLISECONDS_IN_SECONDS)
        }

    source_ip = alert.raw_data.get('_source', {}).get('source.ip')
    if source_ip:
        artifact = {
            'data': source_ip,
            'dataType': 'ip',
            'tags': ['src', alert.use_case, alert.information_system, alert.source],
            'message': 'Source ip address'
        }
        source_port = alert.raw_data.get('_source', {}).get('source.port')
        if source_port:
            artifact['tags'].append(f'port:{source_port}')
        alert.data['artifacts'].append(artifact)

    destination_ip = alert.raw_data.get('_source', {}).get('destination.ip')
    if destination_ip:
        artifact = {
            'data': destination_ip,
            'dataType': 'ip',
            'tags': ['dst', alert.use_case, alert.information_system, alert.source],
            'message': 'Destination ip address'
        }
        destination_port = alert.raw_data.get('_source', {}).get('destination.port')
        if destination_port:
            artifact['tags'].append(f'port:{destination_port}')
        alert.data['artifacts'].append(artifact)

    alert.data['customFields']['observablesCount'] = {
        'integer': len(alert.data['artifacts'])
    }


def craft_qradar_sh_dm_alert(alert: Alert):
    links = craft_links(
        information_system=alert.information_system,
        use_case=alert.use_case,
        playbook_links=alert.playbook_links,
        qradar_offense_id=alert.source_ref
    )
    alert.data = craft_alert(alert)
    alert.data['title'] = f'{alert.use_case_title} ({alert.raw_data.get("offense_source", "")})'
    alert.data['description'] = f"{alert.raw_data.get('description', '')}\n\n{links}"
    alert.data['externalLink'] = config.link_qradar_from_kspd.replace('{id}', alert.source_ref)
    alert.data['customFields']['detectTime'] = {
        'date': alert.raw_data.get('start_time')
    }
    alert.data['customFields']['lastUpdatedTime'] = {
        'date': alert.raw_data.get('last_updated_time')
    }
    alert.data['customFields']['keyField'] = {
        'string': alert.raw_data.get('offense_source', '')
    }


def craft_qradar_sh_vcm_001_alert(alert: Alert):
    links = craft_links(
        information_system=alert.information_system,
        use_case=alert.use_case,
        playbook_links=alert.playbook_links,
        qradar_offense_id=alert.source_ref
    )
    alert.data = craft_alert(alert)
    alert.data['title'] = f'{alert.use_case_title} ({alert.raw_data.get("offense_source", "")})'
    alert.data['description'] = \
        f"Log source ip address: {alert.raw_data['log_source_ip']}\n\n{links}" \
            if 'log_source_ip' in alert.raw_data \
            else links
    alert.data['externalLink'] = config.link_qradar_from_kspd.replace('{id}', alert.source_ref)
    alert.data['customFields']['detectTime'] = {
        'date': alert.raw_data.get('start_time')
    }
    alert.data['customFields']['lastUpdatedTime'] = {
        'date': alert.raw_data.get('last_updated_time')
    }
    alert.data['customFields']['keyField'] = {
        'string': alert.raw_data.get('offense_source', '')
    }


def craft_log_sources_table(log_sources: List[dict]) -> str:
    if not log_sources:
        return ''
    rows = []
    for log_source in log_sources:
        rows.append(f"| {log_source['type_name']} | {log_source['name']} |")
    return '## Log Sources\n|     |     |\n|:--- |:--- |\n%s\n\n'.format('\n'.join(rows))


def craft_log_examples(log_examples: List[str]) -> str:
    if not log_examples:
        return ''
    return '## Log Examples\n```%s```\n\n'.format('\n```\n\n```\n'.join(log_examples))


def craft_qradar_alert(alert: Alert):
    links = craft_links(
        information_system=alert.information_system,
        use_case=alert.use_case,
        playbook_links=alert.playbook_links,
        qradar_offense_id=alert.source_ref
    )
    alert.data = craft_alert(alert)
    alert.data['title'] = f'{alert.use_case_title} ({alert.raw_data.get("offense_source", "")})'
    alert.data['description'] = \
        f"{craft_log_sources_table(alert.raw_data.get('log_sources', []))}" \
        f"{craft_log_examples(alert.log_examples)}" \
        f"{links}"
    alert.data['customFields']['keyField'] = {
        'string': alert.raw_data.get('offense_source', '')
    }
    alert.data['customFields']['logSourceTypes'] = {
        'string': '; '.join(log_source['type_name'] for log_source in alert.raw_data.get('log_sources', []))
    }

    if alert.source_ips:
        for ip in alert.source_ips:
            alert.data['artifacts'].append({
                'data': ip,
                'dataType': 'ip',
                'tags': ['src', alert.use_case, alert.information_system, alert.source],
                'message': 'Source ip address'
            })
    if alert.destination_ips:
        for ip in alert.destination_ips:
            alert.data['artifacts'].append({
                'data': ip,
                'dataType': 'ip',
                'tags': ['dst', alert.use_case, alert.information_system, alert.source],
                'message': 'Destination ip address'
            })
    alert.data['customFields']['observablesCount'] = {
        'integer': len(alert.data['artifacts'])
    }
