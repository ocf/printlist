(function(){
	const RELOAD_TIME = 5000;
	setInterval(loop, RELOAD_TIME);
})();

async function loop(){
	let data = await reload();
	for (let printer_name in data){
		queue(printer_name, data[printer_name]);
	}
}

function element(username, date){
	let wrapper = document.createElement('div');
	wrapper.classList.add('printlist-user');
	let name = document.createElement('div');
	name.classList.add('printlist-user-handle');
	name.innerText = username.replace(/\</g, '&lt;').replace(/\>/g, '&gt;');
	wrapper.appendChild(name);
	return wrapper;
}

function queue(printer_name, data){
	data.sort((a, b)=>{
		// Sorts by date
		return a[1]-b[1];
	})
	.map(item=>([item[0], new Date(item[1]* 1000)]))
	.forEach(item=>{
		let parent = document.querySelector(`.${printer_name} h1`);
		if (document.querySelector(`.${printer_name} .printlist-null`)) document.querySelector(`.${printer_name} .printlist-null`).remove();
		parent.after(element(item[0], item[1]));
		// Do whatever you need, [username, date as Date Object]
	});
}

function reload(){
	return new Promise(async (resolve, reject)=>{		
		var temp = new XMLHttpRequest();
		temp.open('GET','/reload/recent', true);
		temp.send();
		temp.onreadystatechange = ()=>{
			if (temp.readyState === 4) {
				resolve(JSON.parse(temp.response));
			}
		};
	});
}

