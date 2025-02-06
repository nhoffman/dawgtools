WITH base_results AS (
  SELECT
    sdb.SPEC_EPT_PAT_ID as epic_id,
    sdb.CASE_ID as case_id,
    lci.CASE_NUM as case_num,
    res.RESULT_ID,
    c.NAME AS component,
    COMP_RES_UTC_DTTM,
    res.LINE,
    component_value
    FROM uwDAL_Clarity.dbo.SPEC_TEST_REL rel
         JOIN uwDAL_Clarity.dbo.SPEC_DB_MAIN sdb ON sdb.SPECIMEN_ID = rel.SPECIMEN_ID
         JOIN uwDAL_Clarity.dbo.RES_COMPONENTS res ON
                res.RESULT_ID IN (rel.CURRENT_RESULT_ID, rel.VALIDATED_RESULT_ID)
         JOIN uwDAL_Clarity.dbo.CLARITY_COMPONENT c ON c.COMPONENT_ID = res.COMPONENT_ID
         JOIN uwDAL_Clarity.dbo.LAB_CASE_INFO lci ON sdb.CASE_ID = lci.REQUISITION_ID
   WHERE sdb.CASE_ID IS NOT NULL
     AND sdb.SPEC_EPT_PAT_ID IN (%(epic_pat_id)s)
     AND COMP_RES_UTC_DTTM >= %(min_date)s
     AND COMP_RES_UTC_DTTM <= %(max_date)s
)
SELECT DISTINCT
  br.epic_id,
  br.case_num,
  br.COMP_RES_UTC_DTTM as date,
  br.component,
  STRING_AGG(CONVERT(VARCHAR(MAX), MULT_LN_VAL_STG_RAW), '') WITHIN GROUP (ORDER BY rv.GROUP_LINE, rv.VALUE_LINE) AS text
  FROM base_results br
       JOIN uwDAL_Clarity.dbo.RES_VAL_PTR_RM ptr ON ptr.RESULT_ID = br.result_id AND ptr.GROUP_LINE = br.LINE
       JOIN uwDAL_Clarity.dbo.RES_VAL_DATA_RM rv ON br.result_id = rv.RESULT_ID AND rv.GROUP_LINE = ptr.CMP_MULTILINE_VALUE
  -- note that br.case_id is not displayed, but it appears to improve performance when included in the GROUP BY clause
 GROUP BY br.result_id, br.case_id, br.case_num, br.LINE, br.COMP_RES_UTC_DTTM, br.EPIC_ID, br.component

-- select PAT_MRN_ID from uwDAL_Clarity.dbo.PATIENT where EPIC_PAT_ID = '2509889'
