TP3:

1- Exercise 1 and 2 goes toghether because they run together on docker-compose initialization
   Steps:
   
      1- Copy folder Exercise1and2 in a local folder
      2- Run: bash install.sh

2- Exercise 3: create model and table en airflow potgres DB under stock schema

      1- docker inspect db_postgres | grep IPAddress  --> to know postgres DB ip
      2- Modify db.py, change ip address with the one showed above.
      3- Run: poetry install
      4- Run: poetry run python createTables.py

3- Exercice 4: Create a Python class, similar to the `SqLiteClient` of the practical Airflow coursework, 
      in order to connect with the Postgres DB

      1- SqlConnexion.py is parent of SqlPostgresClient and SqLiteClient clases.
      2- Each child class has and if __name__ == "__main__": that lets you test the class.
      3- Run: poetry install, to install dependencies.
      4- To run sqlPostgresCli.py, you must copy .env_postgres as .env in the same directory
      5- Run: docker inspect db_postgres | grep IPAddress  , to know postgres DB ip and replace ip in .env
      6- To run sqLite_cli.py, you must copy .env_sqLite as .env in the same directory, you need 
         to have /tmp/sqlite_default.db created.

4- Exercise 5:

      1- Copy all files to local file from branch Exercise5
      2- Run: bash install.sh --> there are new features, like dockerfile, python librarys to be add,
         .env variables to be use by python-decouple.
      3- In your browser type http://0.0.0.0:8080/  user:airflow, password:airflow
      4- Go to Admin --> Connections. Create a new connection as follow:
            Conn id: postgres_default
            Conn Type: Postgres
            Host: db_postgres
            Schema: airflow
            Login: airflow
            Password: airflow
         Save it.

         Note: Airflow Schema is the name of the database. The stocks_daily table is define in 
              stock schema within airflow database.
      5- Go to Dags and active price_solution. 

         Note: 
            1- price_solution runs only for bussines day. 
            2- The data imported are save in dags/files as json files.  
            3- some times there are problems with the endpoint of the dataset.

5- Exercise 6:

      1- Delete previous docker images of this project from your Linux.
            a) docker image ls
            b) docker image rm <docker-name> 
      2- Delete previous  docker volume of this project from your Linux.
            a) docker volume ls
            b) docker volume rm <volume-name>  
      2- Copy all files to local file from branch Exercise6
      3- Run: bash install.sh --> new library matplotlib was added
      4- In your browser type http://0.0.0.0:8080/  user:airflow, password:airflow
      5- Go to Admin --> Connections. Create a new connection as follow:
            Conn id: postgres_default
            Conn Type: Postgres
            Host: db_postgres
            Schema: airflow
            Login: airflow
         Save it.
      6- Go to Dags and active price_solution.
      7- Plots will be on dags/graphs

6- Exercise 7:

      1- Copy all files to local file from branch Exercise7
      2- In your local file Run: poetry install
      3- Run:  poetry run pip install --upgrade
               poetry run pip install python-decouple SQLAlchemy  psycopg2-binary pandas python-decouple 
               poetry run pip install apache-airflow-providers-docker  apache-airflow-providers-ftp
               poetry run pip install pip install apache-airflow-providers-http apache-airflow-providers-imap 
               poetry run pip install apache-airflow-providers-postgres apache-airflow-providers-sqlite
               poetry run pip install matplotlib         

        Note: poetry add, didn't work for all these files.

      4- From your local file run:  poetry run pytest -v    
      5- You can see errors o problems on /tmp/pytest.log

7- Exercise 8: 

      1- Go to GitHub Actions, select: Exercise 8 Pytest and Pylint, and then do click on Re-run all jobs

      Note: 
         1- pylint is commented, you can uncomment the line and give Re-run all jobs again
         2- On test modules, try and except Exception as e: logging.error(traceback.format_exc()), 
           where comment to make git Actions shows the failure if it happends.