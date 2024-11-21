Quickstart
==========

This repository provides all you need to try the SQAaaS API in a production-like environment. To
this end, we rely on docker-compose to quickly set up the API and all its dependencies, including
the external services.

1. Move to `docker` folder. Here you will find a `docker-compose.yml <>` file that contains the
   definition of all the required services, including the API itself.
   
   .. code-block:: console
   
      $ cd docker/

2. Spawn the services.
   
   .. code-block:: console
   
      $ docker compose up -d

3. Check that all the required services are up & running.

   .. code-block:: console
   
      $ docker compose ps

4. Go ahead and `try out the SQAaaS API! <>`


Troubleshooting
---------------

If you encounter any issues during deployment, `docker compose` could be used to find out the
the exact causes of the errors. We recommend to follow this procedure:

1. List all the services, including the buggy ones that are currently down.

   .. code-block:: console
   
      $ docker compose ps -a

   The output should be similar to the following table:
   
   .. code-block:: console

      NAME         IMAGE                 COMMAND                  SERVICE      CREATED       STATUS       PORTS
      jenkins      jenkins/jenkins:lts   "/usr/bin/tini -- /u…"   jenkins      3 hours ago   Up 3 hours   0.0.0.0:8080->8080/tcp, :::8080->8080/tcp, 0.0.0.0:50000->50000/tcp, :::50000->50000/tcp
      sqaaas-api   docker-sqaaas-api     "docker-entrypoint.s…"   sqaaas-api   3 hours ago   Up 3 hours   0.0.0.0:8082->8082/tcp, :::8082->8082/tcp

2. Look at the `NAME` column. For each service that was not spawned correctly, run:

   .. code-block:: console

      $ docker logs <NAME>

   such as `docker logs sqaaas-api`, which will return the logs provided by the API on startup.
