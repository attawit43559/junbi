"""Builds the unsigned iPhone shortcut "Junbi" (share sheet → Junbi worker /drop).
Sign it on a Mac:  shortcuts sign -m anyone -i Junbi-unsigned.shortcut -o Junbi.shortcut"""
import plistlib, uuid, sys
DROP = 'https://junbi-links.attawit-charoensri.workers.dev/drop'
U = lambda: str(uuid.uuid4()).upper()
u_key, u_b64, u_post, u_msg = U(), U(), U(), U()
def tok(att):   # a text field holding one variable
    return {'Value': {'string': '￼', 'attachmentsByRange': {'{0, 1}': att}}, 'WFSerializationType': 'WFTextTokenString'}
def txt(s):
    return {'Value': {'string': s, 'attachmentsByRange': {}}, 'WFSerializationType': 'WFTextTokenString'}
def item(k, v): return {'WFItemType': 0, 'WFKey': txt(k), 'WFValue': v}
INPUT = {'Type': 'ExtensionInput'}
actions = [
  {'WFWorkflowActionIdentifier': 'is.workflow.actions.gettext',
   'WFWorkflowActionParameters': {'UUID': u_key, 'WFTextActionText': 'ใส่รหัสจาก Junbi'}},
  {'WFWorkflowActionIdentifier': 'is.workflow.actions.base64encode',
   'WFWorkflowActionParameters': {'UUID': u_b64, 'WFBase64LineBreakMode': 'None',
     'WFInput': {'Value': INPUT, 'WFSerializationType': 'WFTextTokenAttachment'}}},
  {'WFWorkflowActionIdentifier': 'is.workflow.actions.downloadurl',
   'WFWorkflowActionParameters': {'UUID': u_post, 'WFURL': DROP, 'WFHTTPMethod': 'POST', 'WFHTTPBodyType': 'JSON', 'ShowHeaders': False,
     'WFJSONValues': {'Value': {'WFDictionaryFieldValueItems': [
        item('action', txt('shareAny')),
        item('key', tok({'Type': 'ActionOutput', 'OutputUUID': u_key, 'OutputName': 'Text'})),
        item('url', tok(INPUT)),
        item('data', tok({'Type': 'ActionOutput', 'OutputUUID': u_b64, 'OutputName': 'Base64 Encoded'})),
     ]}, 'WFSerializationType': 'WFDictionaryFieldValue'}}},
  {'WFWorkflowActionIdentifier': 'is.workflow.actions.getvalueforkey',
   'WFWorkflowActionParameters': {'UUID': u_msg, 'WFGetDictionaryValueType': 'Value', 'WFDictionaryKey': 'message',
     'WFInput': {'Value': {'Type': 'ActionOutput', 'OutputUUID': u_post, 'OutputName': 'Contents of URL'}, 'WFSerializationType': 'WFTextTokenAttachment'}}},
  {'WFWorkflowActionIdentifier': 'is.workflow.actions.notification',
   'WFWorkflowActionParameters': {'WFNotificationActionTitle': 'Junbi',
     'WFNotificationActionBody': tok({'Type': 'ActionOutput', 'OutputUUID': u_msg, 'OutputName': 'Dictionary Value'})}},
]
wf = {
  'WFWorkflowClientVersion': '2607.0.2', 'WFWorkflowMinimumClientVersion': 900, 'WFWorkflowMinimumClientVersionString': '900',
  'WFWorkflowIcon': {'WFWorkflowIconStartColor': 4271458815, 'WFWorkflowIconGlyphNumber': 59511},
  'WFWorkflowTypes': ['ActionExtension'],
  'WFWorkflowInputContentItemClasses': ['WFURLContentItem', 'WFStringContentItem', 'WFImageContentItem', 'WFPDFContentItem', 'WFGenericFileContentItem'],
  'WFWorkflowHasShortcutInputVariables': True,
  'WFWorkflowOutputContentItemClasses': [], 'WFWorkflowHasOutputFallback': False, 'WFQuickActionSurfaces': [],
  'WFWorkflowImportQuestions': [{'ActionIndex': 0, 'Category': 'Parameter', 'DefaultValue': '', 'ParameterKey': 'WFTextActionText',
     'Text': 'วางรหัสจาก Junbi (โปรไฟล์ → รหัสของคุณ) / Paste your code from Junbi'}],
  'WFWorkflowActions': actions,
}
out = sys.argv[1] if len(sys.argv) > 1 else 'Junbi-unsigned.shortcut'
with open(out, 'wb') as f: plistlib.dump(wf, f, fmt=plistlib.FMT_BINARY)
print('wrote', out)
