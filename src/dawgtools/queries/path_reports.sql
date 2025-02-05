WITH base_results AS (
  SELECT
    sdb.SPEC_EPT_PAT_ID as epic_id,
    res.RESULT_ID,
    c.NAME AS component,
    COMP_RES_UTC_DTTM,
    res.LINE,
    component_value
    FROM uwDAL_Clarity.dbo.SPEC_TEST_REL rel
         JOIN uwDAL_Clarity.dbo.SPEC_DB_MAIN sdb ON sdb.SPECIMEN_ID = rel.SPECIMEN_ID AND CASE_ID IS NOT NULL
         JOIN uwDAL_Clarity.dbo.RES_COMPONENTS res ON
                res.RESULT_ID IN (rel.CURRENT_RESULT_ID, rel.VALIDATED_RESULT_ID)
         JOIN uwDAL_Clarity.dbo.CLARITY_COMPONENT c ON c.COMPONENT_ID = res.COMPONENT_ID
   WHERE sdb.SPEC_EPT_PAT_ID IN (%(epic_pat_id)s)
     AND COMP_RES_UTC_DTTM >= %(min_date)s
     AND COMP_RES_UTC_DTTM <= %(max_date)s)

SELECT DISTINCT
  br.epic_id,
  br.COMP_RES_UTC_DTTM as date,
  br.component,
  STRING_AGG(CONVERT(VARCHAR(MAX), MULT_LN_VAL_STG_RAW), '') WITHIN GROUP (ORDER BY rv.GROUP_LINE, rv.VALUE_LINE) AS text
  FROM base_results br
       JOIN uwDAL_Clarity.dbo.RES_VAL_PTR_RM ptr ON ptr.RESULT_ID = br.result_id AND ptr.GROUP_LINE = br.LINE
       JOIN uwDAL_Clarity.dbo.RES_VAL_DATA_RM rv ON br.result_id = rv.RESULT_ID AND rv.GROUP_LINE = ptr.CMP_MULTILINE_VALUE
 GROUP BY br.result_id, br.LINE, br.COMP_RES_UTC_DTTM, br.EPIC_ID, br.component
