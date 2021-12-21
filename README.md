# General information

Main aim of this project is to provide various functionalities useful in student's life. 

## Documents search engine
First implemented functionality is documents search engine. 
Registered users can add images or pdfs. Text is extrected from them using my other app [img2txt][i2t]. Then this text is preprocessed and changed to
word embeddings via my yet another app [language_processing][lp]. Those embeddings are stored in database. 

When user add several files, for instance pdfs from different academic classes, they can search interesting topics and best matching files are displayed.
Search engingine is also implemented in [language_processing][lp] app. Example query might look like this: "class inheritance in python". Then files ranked 
from best to worst match are displayed. This search engine is not perfect that is why it is good to add as many key words to the query as possible. It must also
be noted that for now only documents and queries in polish language are supported.

## Further development
On other branches of this repository I implement other functionalities which will be merged to main branch when they are finished.

## Environment variables
This app needs some environment variables set to run correctly:

- ```EMAIL_PASS=<password to email used for sending emails to registered users>```
- ```EMAIL_USER=<email address used for sending emails to registered users>```
- ```SECRET_KEY=<secret key for flask app>```
- ```SECURITY_PASSWORD_SALT=<pasword salt for flask app>```
- ```SQLALCHEMY_DATABASE_URI=<uri of database>```
- ```URL_IMG=<base url (wthout any endpoints) to img2txt app>```
- ```URL_NLP=<base url (wthout any endpoints) to language_processing app>```
- ```SERVER_NAME=<servername of panelstudenta app>```

[i2t]:<https://github.com/wojciechzyla/img2txt>
[lp]:<https://github.com/wojciechzyla/language_processing>
