CREATE DEFINER=`dokumint`@`%` PROCEDURE `clean`()
BEGIN
SET foreign_key_checks = 0;
TRUNCATE auth_user;
TRUNCATE account_emailaddress;
TRUNCATE account_emailconfirmation;
TRUNCATE socialaccount_socialaccount;
TRUNCATE core_creator;
TRUNCATE core_document;
TRUNCATE core_documentaddress;
TRUNCATE core_documentdate;
TRUNCATE core_documentfinancial;
TRUNCATE core_documentidentifier;
TRUNCATE core_documentkeyvalue;
TRUNCATE core_documentsubtype;
TRUNCATE core_documenttag;
TRUNCATE core_documenttaxlineitem;
TRUNCATE core_documenttype;
TRUNCATE core_documenttypekey;
TRUNCATE core_emailrelaylog;
TRUNCATE core_expenselineitem;
TRUNCATE core_lineitemcategory;
TRUNCATE core_profile;
TRUNCATE core_transactionlog;
TRUNCATE core_userstat;
TRUNCATE core_userfavorite;
SET foreign_key_checks = 1;

INSERT INTO `dokumint`.`core_documenttype`
(`short_code`,
`text`,
`list_template`,
`detail_template`,
`analyze_fn`,
`save_fn`,
`created_on`)
VALUES
('EXP',
'Expense Documents',
'tags/expense_document_list.html',
'expense_document_detail.html',
'_analyze_expense',
'_save_expense',
NOW());

END