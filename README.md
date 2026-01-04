# ReadAssist

A Python webapp to query cloud AI for information on words, from a Kobo e-reader device.

It can ask a remote AI to define a word and provide information on etymology, usage, idioms and other kinds of infromation that a human studying the language might need to know to understand and memorize the word.

The webapp is designed to be invoked from a Kobo e-reader device via Patrick Gaskin's [NickelMenu](https://github.com/pgaskin/NickelMenu) utility, which can customize the Kobo user interface, adding custom menu options and commands.

### Requirements

* An Ollama AI backend, either local or cloud-based
* Web server capable of hosting a Python webapp
* Kobo e-reader device

### Installation/Configuration

##### Web application (readassist.py)

###### Invocation
This is a Python Flask web application, that uses Flask's built-in web server.  To run it, simply invoke it from the shell:

```
python readassist.py
```

It has two command line arguments:

`--host <ip addr>` - Host IP address for this webapp (default `0.0.0.0`)
`--port <port number>` - TCP port for this webapp (default `5000`)

###### Configuration
There are three environment variables to configure its connection to the backend Ollama server.

`RA_OLLAMA_HOST_MAC` - MAC address of the Ollama server, used to send a Wake-on-LAN request to make sure it is awake before making an Ollama query.
`RA_OLLAMA_HOST_IP` - IP address of the Ollama server
`RA_OLLAMA_PORT` - TCP port of the Ollama server (default '11434')

Right now it is assumed the Ollama server is running on a different machine, and is awoken when needed. To disable this behavior, comment out the call to `wake_ollama_server` that appears in `read_assist_web`.  (TODO for further work)

###### Running as a background service
To make it run continually, you will need to install it as a background service.

For Linux, the file `readassist.service` is an example systemd configuration file that you can place into the `~/.config/systemd/user` folder.

To start:
```
systemctl --user daemon-reload
systemctl --user start readassist.service
```

To stop:
```
systemctl --user stop readassist.service
```

To run in the background when system starts:
```
systemctl --user enable readassist.service
```

To check status:
```
systemctl --user status readassist.service 
```

You may also need to enable lingering processes to allow systemd to keep the process running when you log out:

```
loginctl enable-linger $USER
```

Managing systemd is well beyond the scope of this README, but that cheat sheet should be enough to get you started.

#### Kobo Device configuration

* Install the NickelMenu utility on the Kobo device, following the instructions provided on the [NickelMenu website](https://github.com/pgaskin/NickelMenu).

* Here is an example configuration line to add to the NickelMenu `config` file.  Adjust it to taste based on the options described in the next section:

```
menu_item		:selection			:Read Assist	:nickel_browser:modal:http://192.168.0.94:5000/readassist?req_type=translate&req_type=usage&req_type=synonyms&req_type=idioms&text={1|S|%}&lang=it&model=gpt-oss:120b
```

### Options

The script takes the following parameters, as URL parameters on a GET request.

###### `req_type`

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

#### Examples

```
http://localhost:5000/readassist?req_type=translate&req_type=usage&req_type=synonyms&req_type=phrases&lang=it&text=cominciare

http://localhost:5000/readassist?req_type=translate&lang=it&text=cominciare

http://localhost:5000/readassist?req_type=translate&req_type=irregular&req_type=phrases&lang=it&text=invadere
```
