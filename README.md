# ReadAssist

A Python webapp to query cloud AI for information on words, from a Kobo e-reader device

### Requirements

* AI backend (Ollama)
* Web server capable of hosting a Python webapp
* Kobo e-reader device

### Installation/Configuration

XXX setup instructions go here


#### Webserver Host

XXX setup instructions go here

#### Kobo Device

XXX setup instructions go here

### Options

The script takes the following parameters, as URL parameters on a GET request.

###### `req\_type`

One or more of the following one-word tokens that indicates the following type of information to be requested:

* `translate` - translate this word to English, and provide an English definition
* `definition` - provide a definition of this word in its own language
* `etymology` - describe the etymology of this word
* `usage` - provide a description and notes on contemporary usage of this word in its own language
* `history` - give a history of this word, such as when it entered the language
* `phrases` - provide some sample phrases and/or sentences that use this word, in its own language
* `synonyms` - provide a list of synonyms of this word in its own language, including information on shades of differences in meaning
* `cognates` - provide a list of English cognates to this word, if any exist
* `idioms` - provide a list of common idioms that use this word, in its own language
* `irregular` - provide notes about any deviances from standard grammar rules this word may have, that could confuse learners of the language (for example, any irregular conjugations for verbs).

###### `text`

The foreign language text that is the subject of query. This text can be more than one word, so it should be URL-escaped.

###### `lang`

A two-letter code defining the language of the text passed in the `text` parameter, defined by the ISO 639-1 standard.  

###### `model`

Name of the AI model to be queried.

### Examples

```
http://localhost:5000/readassist?req\_type=translate\&req\_type=usage\&req\_type=synonyms\&req\_type=phrases\&lang=it\&text=cominciare

http://localhost:5000/readassist?req\_type=translate\&lang=it\&text=cominciare

http://localhost:5000/readassist?req\_type=translate\&req\_type=irregular\&req\_type=phrases\&lang=it\&text=invadere
```
