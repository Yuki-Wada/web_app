function writeHeader(rootDir){	

	$.ajax({
		url: rootDir + "templates/app/header.html",
		cache: false,
		async: false,
		success: function(html){
			document.write(html);
		}

	});

}



function writeMenu(rootDir){
	
	$.ajax({
		url: rootDir + "templates/app/menu.html",
		cache: false,
		async: false,
		success: function(html){
			document.write(html);
		}

	});

}



function writeFooter(rootDir){
	
	$.ajax({
		url: rootDir + "templates/app/footer.html",
		cache: false,
		async: false,
		success: function(html){
			document.write(html);
		}

	});

}
