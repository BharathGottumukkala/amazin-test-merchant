/* Author:
khornberg
Testing client encryption - kinda of, maybe
*/

function mySubmit(obj) {
  var pwdObj = document.getElementById('password');
  var hashObj = new jsSHA("SHA-256", "TEXT", {numRounds: 1});
  hashObj.update(pwdObj.value);
  var hash = hashObj.getHash("HEX");
  pwdObj.value = hash;
}
