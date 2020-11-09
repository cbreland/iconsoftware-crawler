SCRIPT = """
function main(splash)
  splash:init_cookies(splash.args.cookies)
  assert(splash:go{
    splash.args.url,
    headers=splash.args.headers,
    http_method=splash.args.http_method,
    body=splash.args.body,
    })
  assert(splash:wait(3))

  local entries = splash:history()
  local last_response = entries[#entries].response
  return {
    url = splash:url(),
    headers = last_response.headers,
    http_status = last_response.status,
    cookies = splash:get_cookies(),
    html = splash:html(),
  }
end
"""
SCRIPT_FRAME = """
function main(splash)
  splash:init_cookies(splash.args.cookies)
  assert(splash:go{
    splash.args.url,
    headers=splash.args.headers,
    http_method=splash.args.http_method,
    body=splash.args.body,
    })
  assert(splash:wait(3))
  local entries = splash:history()
  local last_response = entries[#entries].response
  local contentFrame = splash:evaljs("frames[2].document.documentElement.outerHTML")
  local leftFrame = splash:evaljs("frames[1].document.documentElement.outerHTML")
  local topFrame = splash:evaljs("frames[0].document.documentElement.outerHTML")
  return {
    url = splash:url(),
    headers = last_response.headers,
    http_status = last_response.status,
    cookies = splash:get_cookies(),
    html = splash:html(),
    frames = {frame_1 = contentFrame, frame_2 = leftFrame, frame_3 = topFrame} 
  }
end
"""
FIELDNAMES = [
    'case_number', 'status', 'disp_date', 'disp_stage', 'disp_code', 'type_of_case', 'case_types', 'style_of_case', 'cause_of_action', 'principal_claim',
    'interest', 'interest_other', 'attorney_fees', 'filing_cost_serve', 'fi_fa_fee', 'totals', 'fi_fa_notes', 'types_on_this_case', 'cse', 'judge',
    'case_status', 'service_date', 'answer_date', 'projected_default_date', 'disposition_date', 'stage_of_disposition', 'disposition_code',
    'last_updated_by', 'updated_on', 'plaintiff', 'served_status',  'last_name', 'first_name', 'middle_name', 'suffix', 'full_name',
    'unique_case_number', 'street',  'street2', 'city', 'state', 'zip', 'home_phone', 'work_phone', 'email', 'party_type', 'service_type', 'filename'
]