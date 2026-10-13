ps ax | grep gunicorn
echo "Do you wish to kill all gunicorn processes?"
select yn in "Yes" "No"; 
do
    case $yn in
        Yes ) pkill gunicorn; break;;
        No ) exit;;
    esac
done
echo "Do you wish to start gunicorn server?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) gunicorn dokumint.wsgi:application --name dokumint --workers 3 --user=ec2-user --group=ec2-user --bind=127.0.0.1:8000 --daemon; break;;
        No ) exit;;
    esac
done
