$(document).ready(function(){
	const host = "ws://192.168.11.16:8889/test";
	let ws = new WebSocket(host);

	$("#sendBtn").on("click", send_message);
	var canvas = document.getElementById("myCanvas");
	var width = canvas.width;
	var height = canvas.height;
	var ctx = canvas.getContext("2d");

	const back_index = 29;
	var back_image;
	// 分割後のデータを保存する
	var imgList = [];

	var get_card_image = function(card)
	{
		let mark = card['mark'] - 1;
		let number = card['number'] - 1;

		let index = number + mark * 15
		var img = imgList[index];
		return img;
	};

	ws.onopen = load_image;

	function load_image() {
		// 分割する幅と高さを指定する
		// 画像を割り切れれば幅と高さは何でもよい
		var width = 32, height = 64;
		//画像の取得からロード後処理まで
		var img = new Image();
		img.src = "static/images/cards.png";
		img.onload = function() {
			segmentationImage(img, width, height);
		}
	}

	function segmentationImage(img, width, height) {
		// 分割用のキャンバスを作成する
		// 画面には表示されない
		let canvas = $("<canvas width=" + width + " height=" + height + ">").get(0);
		let ctx = canvas.getContext("2d");
		// 縦横の個数を取得する
		let wLength = img.width / width;
		let hLength = img.height / height;
		// 分割数だけリストに入れる
		for(let num = 0; num < wLength * hLength; num++) {
			ctx.clearRect(0,0,canvas.width,canvas.height);
			ctx.drawImage(img, width * (num % wLength), height * Math.floor(num / wLength), width, height, 0, 0, width, height);
			let img_piece = new Image();
			img.width = 32;
			img.height = 64;
			img_piece.src = canvas.toDataURL();
			imgList.push(img_piece);
		}
		send_message();
	}

	function send_message()
	{
		message = {};
		message['type'] = 'initialize_page';
		ws.send(JSON.stringify(message));
	}

	function on_recieve_message(message){
		var received_message_data = JSON.parse(message.data);
		var participant_count = received_message_data['participant_count'];

		if (received_message_data['type'] == 'initialize_page')
		{
			$("#participant_count").html('現在 ' + participant_count + ' 人の方が参加しています。' );
			$("#show").empty();
			if (participant_count >= 2)
			{
				let button = $('<button>').attr('type', 'button').attr('id', 'start').html('ゲームスタート');
				button.click(function(){
					sending_message = {};
					sending_message['type'] = 'initialize_game';
					ws.send(JSON.stringify(sending_message));
				});
				$("#show").append(button);
			}	
		}
		else if (received_message_data['type'] == 'initialize_game')
		{
			start_field(received_message_data);
		}
		else if (received_message_data['type'] == 'bet')
		{
			bet(received_message_data);
		}
	};

	function makeBetButton(message_data){
		$("#show").empty();
		$("#show").append(message_data['money']);
		$("#show").append(message_data['bet']);	
		if (message_data['bet_now'])
		{
			let text_box = $('<input type="number" id="bet_amount"><br>');
			$("#show").append(text_box);

			let hold_down_button = $('<button>').attr('type', 'button').attr('id', 'start').html('ホールドダウン');
			hold_down_button.click(function(){
				sending_message = {};
				sending_message['type'] = 'bet';
				sending_message['amount'] = parseInt($('#bet_amount').val());
				ws.send(JSON.stringify(sending_message));
			});
			$("#show").append(hold_down_button);

			
			let check_button = $('<button>').attr('type', 'button').attr('id', 'start').html('チェック');
			check_button.click(function(){
				sending_message = {};
				sending_message['type'] = 'bet';
				sending_message['amount'] = parseInt($('#bet_amount').val());
				ws.send(JSON.stringify(sending_message));
			});
			$("#show").append(check_button);

			let call_button = $('<button>').attr('type', 'button').attr('id', 'start').html('コール');
			call_button.click(function(){
				sending_message = {};
				sending_message['type'] = 'bet';
				sending_message['amount'] = parseInt($('#bet_amount').val());
				ws.send(JSON.stringify(sending_message));
			});
			$("#show").append(call_button);

			let raise_button = $('<button>').attr('type', 'button').attr('id', 'start').html('レイズ');
			raise_button.click(function(){
				sending_message = {};
				sending_message['type'] = 'bet';
				sending_message['amount'] = parseInt($('#bet_amount').val());
				ws.send(JSON.stringify(sending_message));
			});
			$("#show").append(raise_button);
		}
	}

	function start_field(message_data){
		var x = 0;
		makeBetButton(message_data);

		for (session_id in message_data['field'])
		{
			$("#info").append(
				'<table><tbody>' +
				'<tr><td>Session ID</td><td>' + session_id + '</td></tr>' +
				'<tr><td>Money</td><td class="money ' + session_id + '">' + message_data['field'][session_id]['money'] + '</td></tr>' +
				'<tr><td>Bet</td><td class="bet ' + session_id + '">' + message_data['field'][session_id]['bet'] + '</td></tr>' +
				'</tbody></table>'
			);
		}

		let common_cards = [];
		for (let card_id of message_data['common']['card']['number'])
		{
			common_cards.push(card_id);
		}
		let my_cards = [];
		for (let card_id of message_data['my_field']['card']['number'])
		{
			my_cards.push(card_id);
		}
		function render(){
			ctx.clearRect(0, 0, width, height);
			for (let i = 0; i < common_cards.length; ++i)
			{
				let common_card = common_cards[i];
				ctx.drawImage(get_card_image(common_card), 120 + 60 * i - 16, 180 - 24, 32, 64);
			}
			for (let i = 0; i < my_cards.length; ++i)
			{
				let my_card = my_cards[i];
				ctx.drawImage(get_card_image(my_card), 120 + 60 * i - 16, 300 - 24, 32, 64);
			}
		};
		render();
		//let timer = setInterval(render, 20);
	};

	function bet(message_data)
	{
		makeBetButton(message_data);

		let session_id = message_data['bet_info']['bettor'];
		let amount = message_data['bet_info']['bet_amount'];
		let money_selector = $('td.' + session_id + '.money');
		money_selector.html(parseInt(money_selector.html()) - amount);
		let bet_selector = $('td.' + session_id + '.bet');
		bet_selector.html(parseInt(bet_selector.html()) + amount);
	}

	function draw_field(){
		var x = 0;
		function render(){

			ctx.clearRect(0, 0, width, height);
			for (let i = 0; i < 10; ++i)
			{
				ctx.drawImage(back_image, 300 - 16, 180 - (i - 5) - 24, 32, 64);
			}
			for (let i = 0; i < global_card_images.length; ++i)
			{
				ctx.drawImage(global_card_images[i], 180 + i * 60 - 16, 180 - 24, 32, 64);
			}

			for (let i = 0; i < 5; ++i)
			{
				ctx.drawImage(back_image, 120 + 60 * i - 16, 60 - 24, 32, 64);
			}
			for (let i = 0; i < my_card_images.length - 1; ++i)
			{
				ctx.drawImage(my_card_images[i], 120 + 60 * i - 16, 300 - 24, 32, 64);
			}

			if (x < 100)
			{
				ctx.drawImage(back_image, 300 - 16 + 60 / 100 * x, 180 - 5 - 24 + (120 + 5) / 100 * x, 32, 64);
				x += 5;
			}
			else
			{
				ctx.drawImage(my_card_images[4], 300 - 16 + 60 / 100 * x, 180 - 5 - 24 + (120 + 5) / 100 * x, 32, 64);
				clearInterval(timer);
			}
		};
		let timer = setInterval(render, 20);
	}

	ws.onmessage = on_recieve_message;
});
