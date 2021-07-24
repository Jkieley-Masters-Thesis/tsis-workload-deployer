import logging
import os
import random
import threading
import uuid

import chevron
import yaml

from pclusterutils import LogUtil
from sflower import Clusters
from sflower import IOUtils

LogUtil.config_loggin("deployer.log")


def main():
    deployments_train = [
        {
            'name': 'deploy_arput_job',
            'type': 'train',
            'multiplier': 10,
            'deployment_function': deploy_arput_job,
            'repeat_int': 180.0
        },
        {
            'name': 'deploy_savedt_job',
            'type': 'train',
            'multiplier': 10,
            'deployment_function': deploy_savedt_job,
            'repeat_int': 160.0
        },
        {
            'name': 'deploy_cfdwid_lr_train_job',
            'type': 'train',
            'multiplier': 10,
            'deployment_function': deploy_cfdwid_lr_train_job,
            'repeat_int': 140.0
        }
    ]

    deployments_inference = [
        {
            'name': 'deploy_arpui_job',
            'type': 'inf',
            'max_count': 20,
            'multiplier': 20,
            'deployment_function': deploy_arpui_job,
            'repeat_int_min': 0,
            'repeat_int_max': 1800,
        },
        {
            'name': 'deploy_savedi_job',
            'type': 'inf',
            'max_count': 20,
            'multiplier': 20,
            'deployment_function': deploy_savedi_job,
            'repeat_int_min': 0,
            'repeat_int_max': 1800,
        },

        {
            'name': 'deploy_cfdwid_lr_inference_job',
            'type': 'inf',
            'max_count': 20,
            'multiplier': 20,
            'deployment_function': deploy_cfdwid_lr_inference_job,
            'repeat_int_min': 0,
            'repeat_int_max': 1800,
        },
    ]

    logging.info("starting with config: " + str([deployments_inference, deployments_train]))

    for deployment in deployments_train:
        # range equals "how many times to iterate" 0 == no iterations, 1 equals 1 loops, 2 equals 2 loops etc.
        repeat_interval = 0
        for x in range(deployment['multiplier']):
            schedule_for_the_future(deployment, repeat_interval)
            repeat_interval += deployment['repeat_int']

    for deployment in deployments_inference:
        repeat_interval = 0
        for x in range(deployment['multiplier']):
            schedule_for_the_future(deployment, repeat_interval)
            repeat_interval = random.randint(deployment['repeat_int_min'], deployment['repeat_int_max'])


def schedule_for_the_future(deployment, repeat_interval):
    logging.info(
        "scheduling deployment: %s in this many seconds: %s" % (deployment['name'], str(repeat_interval)))
    threading.Timer(repeat_interval, deploy, [deployment]).start()


def deploy(deployment):
    logging.info("deploying: deployment['name']: " + deployment['name'])
    logging.info("deploying:  deployment['type']: " + deployment['type'])
    safe_deploy(deployment)


def safe_deploy(deployment):
    logging.info('starting')
    cluster = Clusters.get_scale_from_cluster()
    deployment['deployment_function'](cluster)


# deploy_savedi_job(cluster, get_trained_models("Trained_Saved_Model")["name"],get_trained_models("Trained_Arpu_Model")["name"])
def deploy_savedi_job(cluster):
    # deployment specific vars
    deployment_yaml_file = os.environ['SAVEDI_JOB_YAML']
    deployment_name = "savedi"
    deployment_uuid = str(uuid.uuid4())
    template_inputs = {
        'runId': deployment_uuid
    }

    deploy_generic_job(deployment_name, deployment_uuid, deployment_yaml_file, template_inputs, cluster)


def deploy_arput_job(cluster):
    # deployment specific vars
    deployment_yaml_file = os.environ['ARPUT_JOB_YAML']
    deployment_name = "arput"
    deployment_uuid = str(uuid.uuid4())
    template_inputs = {
        'runId': deployment_uuid
    }

    deploy_generic_job(deployment_name, deployment_uuid, deployment_yaml_file, template_inputs, cluster)


def deploy_arpui_job(cluster):
    # deployment specific vars
    deployment_yaml_file = os.environ['ARPUI_JOB_YAML']
    deployment_name = "arpui"
    deployment_uuid = str(uuid.uuid4())
    template_inputs = {
        'runId': deployment_uuid
    }

    deploy_generic_job(deployment_name, deployment_uuid, deployment_yaml_file, template_inputs, cluster)


def deploy_savedt_job(cluster):
    # deployment specific vars
    deployment_yaml_file = os.environ['SAVEDT_JOB_YAML']
    deployment_name = "savedt"
    deployment_uuid = str(uuid.uuid4())
    template_inputs = {
        'runId': deployment_uuid
    }

    deploy_generic_job(deployment_name, deployment_uuid, deployment_yaml_file, template_inputs, cluster)


def deploy_generic_job(deployment_name, deployment_uuid, deployment_yaml_file, template_inputs, cluster):
    logging.info("Preparing Job deployment")
    logging.info("Preparing Job deployment: deployment_name: " + deployment_name)
    logging.info("Preparing Job deployment: deployment_uuid: " + deployment_uuid)
    logging.info("Preparing Job deployment: deployment_yaml_file: " + deployment_yaml_file)
    logging.info("Preparing Job deployment: template_inputs: " + str(template_inputs))

    template_text = IOUtils.read_text_file(deployment_yaml_file)
    output = chevron.render(template_text, template_inputs)
    deployment_yaml = yaml.safe_load(output)
    deployment_yaml['metadata']['name'] = deployment_name + '--' + deployment_uuid

    logging.info("Deploying Job '%s'" % deployment_yaml['metadata']['name'])
    res = cluster.create_job_from_yaml(deployment_yaml)

    logging.info("Job created. status='%s'" % res.metadata.name)


def deploy_cfdwid_lr_train_job(cluster):
    # deployment specific vars
    deployment_yaml_file = os.environ['CFDWID_LR_TRAIN_JOB_YAML']

    deployment_name = "cfdwid-lr-train"
    deployment_uuid = str(uuid.uuid4())
    template_inputs = {
        'runId': deployment_uuid
    }

    deploy_generic_job(deployment_name, deployment_uuid, deployment_yaml_file, template_inputs, cluster)


def deploy_cfdwid_lr_inference_job(cluster):
    # deployment specific vars
    deployment_yaml_file = os.environ['CFDWID_LR_INFERENCE_JOB_YAML']

    deployment_name = "cfdwid-lr-inference"
    deployment_uuid = str(uuid.uuid4())
    template_inputs = {
        'runId': deployment_uuid
    }

    deploy_generic_job(deployment_name, deployment_uuid, deployment_yaml_file, template_inputs, cluster)


if __name__ == '__main__': main()
