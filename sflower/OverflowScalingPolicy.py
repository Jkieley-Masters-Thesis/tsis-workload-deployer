import logging
import math
import os

from sflower import Clusters


def overflow_scale_policy():
    f_cluster = Clusters.get_scale_from_cluster()
    pending_pods, is_cluster_overwhelmed_bool = is_cluster_overwhelmed(f_cluster)
    if is_cluster_overwhelmed_bool:
        Clusters.create_scale_to_cluster(pending_pods, 1.0)
        # cluster creation takes on avg 8mins, alot can change in 8mins and we should refetch the pending pods
        # before we proceed.
        pending_pods, is_cluster_overwhelmed_bool = is_cluster_overwhelmed(f_cluster)

        Clusters.copy_aws_to_cluster_data()
        t_clusters = Clusters.get_scale_to_cluster()
        pending_jobs = get_jobs_from_pods(f_cluster, pending_pods)

        spread_jobs(pending_jobs, f_cluster, t_clusters, 1.0)


def is_cluster_overwhelmed(scale_from_cluster):
    pending_pods = scale_from_cluster.get_pending_pods()
    pending_pod_len = len(pending_pods)
    is_cluster_overwhelmed_bool = pending_pod_len > 0

    logging.info("pending_pods len: " + str(pending_pod_len))
    logging.info("is_cluster_overwhelmed_bool: " + str(is_cluster_overwhelmed_bool))

    return pending_pods, is_cluster_overwhelmed_bool


def move_load_to_from(deployment_clustera, clustera_client, clusterb_client):
    deployment_clusterb = clusterb_client.duplicate_deployment(deployment_clustera)
    clusterb_client.increment_replica(deployment_clusterb)
    clustera_client.decrement_replica(deployment_clustera)


def onschedule_cheapest_cluster():
    # are there any mcs-deployments, that have not been scheduled (cluster attribute is not populated)?
    clusters = Clusters.get_scale_to_clusters()  # get clusters crds
    if Clusters.scale_to_cluster_exists(clusters):  # checks if crds exist
        scale_to_cluster, scale_to_crd = Clusters.get_scale_to_cluster(clusters)
        description = Clusters.get_cluster_description(scale_to_crd)
        logging.info("scale to cluster already exists: " + description)
    else:
        logging.info("creating scale to cluster")
        clusters = Clusters.create_scale_to_cluster_cheapest_by_instance_region()

    # spread_deployments(cluster_scale_from, clusters, pending_pods, pod_mapping)
    return None


def spread_jobs(pending_jobs, f_cluster, t_clusters, percent_to_move):
    move_jobs(f_cluster, pending_jobs, t_clusters, percent_to_move)


def move_jobs(f_cluster, pending_jobs, t_clusters, percent_to_move):
    pending_jobs_len = len(pending_jobs)
    number_of_pods_to_move = math.ceil(pending_jobs_len * percent_to_move)
    move_cursor = 0

    logging.info("pending_jobs_len: " + str(pending_jobs_len))
    logging.info("number_of_pods_to_move: " + str(number_of_pods_to_move))
    logging.info("move_cursor: " + str(move_cursor))

    for x in range(0, pending_jobs_len):
        job = pending_jobs[x]
        if move_cursor < number_of_pods_to_move:
            logging.info("move_cursor: " + str(move_cursor) + ", moving job to cluster: " + job.metadata.name)
            t_clusters.duplicate_job(job)
            f_cluster.delete_job(job)
            f_cluster.delete_pods_from_job(job)  # this is critical
        else:
            logging.info("move_cursor: " + str(move_cursor) + ", job staying queued: " + job.metadata.name)
        move_cursor = move_cursor + 1


def get_jobs_from_pods(scale_from_cluster, pending_pods):
    logging.info("pending pods")
    pods_by_job_name = {}
    for pending_pod in pending_pods:
        pods_by_job_name[pending_pod.metadata.labels['job-name']] = ''

    pending_jobs = []
    jobs = scale_from_cluster.get_jobs()
    for job in jobs:
        # pending pod matches job
        if job.metadata.name in pods_by_job_name:
            pending_jobs.append(job)
    return pending_jobs
