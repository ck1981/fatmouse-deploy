var express = require('express');
var app = express();

app.get('/', function(req, res){
      res.send('Nodejs app');
});

app.listen(3000);
