const serverIP = 'http://154.8.196.163:8180'

function hideInfo () {
  owo.script.page.view.content._list[owo.script.page.view.content._activeIndex].$el.querySelector('.hide-box').style.display = 'none'
  owo.script.page.view.content._list[owo.script.page.view.content._activeIndex].$el.querySelector('.list').style.display = 'block'
}