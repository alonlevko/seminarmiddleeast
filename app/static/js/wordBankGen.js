var word_list = []

function addWord() {
	var input = document.getElementById("word_bank_gen_word");
	var new_word = input.value;
	input.value = "";
	if (word_list.some(word => (word === new_word))){
		return;
	}
	word_list.push(new_word);
	var div = document.getElementById("word_bank_gen");
	var button = document.createElement("button");
	button.innerHTML = new_word;
	var removeButton = 	function() {
		const index = word_list.indexOf(new_word);
		if (index > -1) {
			word_list.splice(index, 1);
		}
		this.remove();
	}
	button.addEventListener("click", removeButton);
	div.appendChild(button);
}
