import multiprocessing

import click

from helpers import config_helper
from workers import db_worker
from workers import slack_worker


def create_worker(workers, worker_name, worker_func, worker_args):
    worker = multiprocessing.Process(
        name=worker_name,
        target=worker_func,
        args=worker_args)
    workers.append(worker)
    return worker


@click.command()
@click.option('-d', '--debug', is_flag=True, default=False)
@click.option('-v', '--verbose', is_flag=True, default=False)
def main(debug, verbose):
    click.echo('Debug: %s' % debug)
    click.echo('Verbosity: %s' % verbose)
    config = config_helper.get_config(debug=debug)

    workers = []

    create_worker(workers, "slack_worker", slack_worker.run, (config, "slack", verbose))

    if config_helper.is_worker_active(config, "voltdb"):
        create_worker(workers, "voltdb_worker", db_worker.run, (config, "voltdb", verbose))

    if config_helper.is_worker_active(config, "timesten"):
        create_worker(workers, "timesten_worker", db_worker.run, (config, "timesten", verbose))

    if config_helper.is_worker_active(config, "altibase"):
        create_worker(workers, "altibase_worker", db_worker.run, (config, "altibase", verbose))

    for w in workers:
        print('Starting worker for {}.'.format(w.name))
        w.start()

    for w in workers:
        w.join()
        print("Worker={worker_name} ExitCode={worker_exit_code}".format(
            worker_name=w.name,
            worker_exit_code=w.exitcode))


if __name__ == "__main__":
    main()
