'use strict'

// server.js

//var pythonShell = require('python-shell')

/*
var defaultOptions = {
	mode: 'text',
};
*/

var spawn = require('child_process').spawn;

// call packages
var express = require('express');
var app = express();

// use body-parser to get data from POST requests
/*
var bodyParser = require('body-parser');
app.use(bodyParser.urlencoded({ extendd: true }));
app.use(bodyParser.json());
*/

var port = 8080;
//var port = 80;

// Define the routes
var router = express.Router();

// GET endpoint for sanity
router.get('/', function(req, res) {
	res.json({message: 'working'});
});

router.get('/locate/:index', function(req, res) {
	var index = req.params.index
	console.log('hello' + index)
	var py = spawn('python', ['/home/pi/Desktop/Adafruit_DotStar_Pi/flashLED.py', index])
	
	/*
	var options = {
		mode: 'text',
		scriptPath: '/home/pi/Desktop/Adafruit_DotStar_Pi/',
		args: [index]
	};

	var ps = new pythonShell('flashLED.py', options)
		.end(function(){
			console.log('finished');
			res.json({message: 'done'});
		});
	*/

	res.json({message: 'done'});
});

app.use('/api', router);

app.listen(port);
console.log('port: ' + port);

