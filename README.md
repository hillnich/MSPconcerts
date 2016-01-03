#### Configuration

1. Input files need to have `example` stripped off from them:

  ```
  email.from.example  -> email.from
  email.to.example    -> email.to
  bandlist.in.example -> bandlist.in
  ```
  
2. Input files listed above should be edited to fit your needs.
  * `email.from` should list an email and password representing the alert sender
  * `email.to` should be a list of emails corresponding to recipients of alert emails
  * `bandlist.in` is list of bands of interest. Case does not matter, as the search is a case-insensitive grep

#### Execution

Execute with the following:
```
python MSPconcerts.py
```
#### Known Issues

I haven't carefully handled UTF-8 characters. So, any band name with non-ASCII characters will probably not get matched, unless you just truncate the band name at the first appearance of a non-ASCII character.

#### Dependent Python Modules and Libraries
```
BeautifulSoup4
requests
html5lib
```