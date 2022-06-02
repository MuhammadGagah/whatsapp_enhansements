import appModuleHandler
import api
from scriptHandler import script
from ui import message
import controlTypes
from keyboardHandler import KeyboardInputGesture
import addonHandler
import os
import winsound
from gui import SettingsPanel, NVDASettingsDialog, guiHelper
import wx
import config


addonHandler.initTranslation()

path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "sounds"))


spec = {"record_sounds": "boolean(default=true)"}
config.confspec["whatsapp_enhansements"] = spec


class SettingsPanel(SettingsPanel):
	title = "whatsapp enhansements"
	def makeSettings(self, settingsSizer):
		sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		self.recordSounds = sHelper.addItem(wx.CheckBox(self, -1, "مؤثرات التسجيل", name="record_sounds"))
		self.recordSounds.Value = config.conf["whatsapp_enhansements"]["record_sounds"]

	def postInit(self):
		self.recordSounds.SetFocus()
	def onSave(self):
		for control in self.GetChildren():
			if type(control) == wx.CheckBox:
				config.conf["whatsapp_enhansements"][control.Name] = control.Value


class AppModule(appModuleHandler.AppModule):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		NVDASettingsDialog.categoryClasses.append(SettingsPanel)
	def find(self, automationId):
		fg = api.getForegroundObject().children[1]
		for obj in fg.children:
			if obj.UIAAutomationId == automationId:
				return obj

	@script(
		gesture="kb:alt+t", 
		description=_("read the chat subtitle"), 
		category="whatsapp")
	def script_subtitles(self, gesture):
		obj = self.find("TitleButton")
		if obj:
			message(", ".join([o.name for o in obj.children]))
		else:
			gesture.send()

	@script(
		gesture="kb:alt+i", 
		description=_("open chat info"), 
		category="whatsapp")
	def script_info(self, gesture):
		obj = self.find("TitleButton")
		if obj:
			obj.doAction()
		else:
			gesture.send()

	@script(
		gesture="kb:control+o", 
		description=_("Attach item"), 
		category="whatsapp")
	def script_attach(self, gesture):
		obj = self.find("AttachButton")
		if obj:
			obj.doAction()
		else:
			gesture.send()

	@script(
		gesture="kb:alt+u", 
		description=_("go to the unread messages section"), 
		category="whatsapp")
	def script_unread(self, gesture):
		def search(txt):
			words = ["غير مقرو", "unread"]
			for word in words:
				if txt.find(word) != -1:
					return word
			return -1
		obj = self.find("ListView")
		if obj:
			for msg in obj.children[::-1]:
				if len(msg.children) == 1 and search(msg.name) != -1:
					msg.next.setFocus()
					break
			else:
				message("لا توجد رسائل جديدة غير مقروءة")
		else:
			gesture.send()

	@script(
		gesture="kb:alt+m",
		description=_("go to the messages list"),
		category="whatsapp")

	def script_messagesList(self, gesture):
		obj = self.find("ListView")
		if obj:
			obj.lastChild.setFocus() if obj.childCount > 0 else obj.setFocus()
		else:
			gesture.send()


	@script(
		gesture="kb:alt+c",
		description=_("go to the chats list"),
		category="whatsapp")
	def script_chatsList(self, gesture):
		obj = self.find("ChatList")
		if obj:
			obj = obj.children[0]
			for chat in obj.children:
				if controlTypes.STATE_SELECTED in chat.states:
					chat.setFocus()
					break
			else:
				obj.setFocus()
		else:
			gesture.send()

	@script(
		gesture="kb:control+n",
		description=_("new chat"),
		category="whatsapp")
	def script_newChat(self, gesture):
		obj = self.find("NewConvoButton")
		if obj:
			obj.doAction()
		else:
			gesture.send()

	@script(
		gesture="kb:alt+e",
		description=_("go to the typing message text field"),
		category="whatsapp")
	def script_messageField(self, gesture):
		obj = self.find("TextBox")
		if obj:
			obj.setFocus()
		else:
			gesture.send()

	@script(
		gesture="kb:control+r",
		description=_("record voice notes"),
		category="whatsapp")
	def script_record(self, gesture):
		txt = self.find("TextBox")
		obj = self.find("RightButton") or self.find("PttSendButton")
		if obj and (txt is None or len(txt.children) > 0):
				obj.doAction()
				if config.conf["whatsapp_enhansements"]["record_sounds"]:
					winsound.PlaySound(os.path.join(path, "record.wav"), 1) if obj.UIAAutomationId == "RightButton" else winsound.PlaySound(os.path.join(path, "stop.wav"), 1)
		else:
			gesture.send()

	@script(
		gesture="kb:control+shift+r",
		description=_("delete voice notes"),
		category="whatsapp")
	def script_recordDelete(self, gesture):
		obj = self.find("PttDeleteButton")
		if obj:
			obj.doAction()
			winsound.PlaySound(os.path.join(path, "error.wav"), 1) if config.conf["whatsapp_enhansements"]["record_sounds"] else None
		else:
			gesture.send()



	def event_gainFocus(self, obj, nextHandler):
		if obj.name in ("WhatsApp.GroupParticipantsItemVm", "WhatsApp.ChatListMessageSearchCellVm", "WhatsApp.ChatListGroupSearchCellVm", "WhatsApp.Pages.Recipients.UserRecipientItemVm"):
			obj.name = ", ".join([m.name for m in obj.children])
		elif obj.UIAAutomationId == "MuteDropdown":
			obj.name = obj.children[0].name
		elif obj.UIAAutomationId == "ThemeCombobox":
			obj.name = obj.previous.name
		elif obj.UIAAutomationId == "BackButton":
			obj.name = _("back")
		elif obj.UIAAutomationId == "PttDeleteButton":
			obj.name = _("cancel recording")
		elif obj.name == "WhatsApp.ChatListArchiveButtonCellVm":
			obj.name = _("archived chats")

		nextHandler()
	def terminate(self):
		NVDASettingsDialog.categoryClasses.remove(SettingsPanel)