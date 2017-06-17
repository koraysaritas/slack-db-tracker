import multiprocessing

import click

from helpers import config_helper
from workers import altibase_worker
from workers import slack_worker
from workers import timesten_worker
from workers import voltdb_worker


def start_worker(workers, worker_name, worker_func, worker_args):
    worker = multiprocessing.Process(
        name=worker_name,
        target=worker_func,
        args=worker_args)
    workers.append(worker)
    worker.start()
    return worker


@click.command()
@click.option('-d', '--debug', is_flag=True, default=False)
@click.option('-v', '--verbose', is_flag=True, default=False)
def main(debug, verbose):
    click.echo('Debug: %s' % debug)
    click.echo('Verbosity: %s' % verbose)
    config = config_helper.get_config(debug=debug)

    workers = []

    start_worker(workers, "slack_worker.run", slack_worker.run, (config, "slack"))

    if config_helper.is_worker_active(config, "voltdb"):
        print('Starting worker for VoltDB.')
        start_worker(workers, "voltdb_worker.run", voltdb_worker.run, (config, "voltdb"))

    if config_helper.is_worker_active(config, "timesten"):
        print('Starting worker for TimesTen.')
        start_worker(workers, "timesten", timesten_worker.run, (config, "timesten"))

    if config_helper.is_worker_active(config, "altibase"):
        print('Starting worker for Altibase.')
        start_worker(workers, "altibase_worker.run", altibase_worker.run, (config, "altibase"))

    for w in workers:
        w.join()
        print("worker={worker_name} exitcode={worker_exit_code}".format(
            worker_name=w.name,
            worker_exit_code=w.exitcode))


if __name__ == "__main__":
    main()
