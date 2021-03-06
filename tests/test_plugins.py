from textwrap import dedent
from beancount.loader import load_file, load_string
from fava.plugins.link_statements import StatementDocumentError


def test_plugins(tmpdir):
    sample_folder = tmpdir.mkdir('fava_plugins')

    documents_folder = sample_folder.mkdir('documents')

    foo_folder = documents_folder.mkdir('Expenses').mkdir('Foo')
    sample_statement1 = foo_folder.join('2016-11-01 Test 1.pdf')
    sample_statement1.write('Hello World 1')
    sample_statement2 = foo_folder.join('2016-11-01 Test 2.pdf')
    sample_statement2.write('Hello World 2')
    sample_statement3 = foo_folder.join('2016-11-01 Test 3 discovered.pdf')
    sample_statement3.write('Hello World 3')

    assets_folder = documents_folder.mkdir('Assets').mkdir('Cash')
    sample_statement4 = assets_folder.join('2016-11-01 Test 4.pdf')
    sample_statement4.write('Hello World 4')
    sample_statement5 = assets_folder.join('Test 5.pdf')
    sample_statement5.write('Hello World 5')

    beancount_file = sample_folder.join('example.beancount')
    beancount_file.write(dedent("""
        option "title" "Test"
        option "operating_currency" "EUR"
        option "documents" "{}"

        plugin "fava.plugins.link_statements"
        plugin "fava.plugins.tag_discovered_documents"

        2016-10-31 open Expenses:Foo
        2016-10-31 open Assets:Cash

        2016-11-01 * "Foo" "Bar"
            statement: "{}"
            Expenses:Foo                100 EUR
            Assets:Cash

        2016-11-02 * "Foo" "Bar"
            statement: "documents/Expenses/Foo/2016-11-01 Test 1.pdf"
            statement-2: "documents/Assets/Cash/2016-11-01 Test 4.pdf"
            Expenses:Foo        100 EUR
            Assets:Cash

        2016-11-02 document Assets:Cash "documents/Assets/Cash/Test 5.pdf"
    """.format(documents_folder, sample_statement2)))

    entries, errors, options = load_file(str(beancount_file))

    assert len(errors) == 0
    assert len(entries) == 9

    assert 'statement' in entries[3].tags
    assert 'statement' in entries[4].tags
    assert 'statement' in entries[5].tags

    assert entries[2].links == entries[5].links
    assert entries[7].links == entries[3].links == entries[4].links

    assert 'discovered' in entries[6].tags
    assert not entries[8].tags


def test_link_statements_no_documents(load_doc):
    """
    plugin "fava.plugins.link_statements"

    2016-10-31 open Expenses:Foo
    2016-10-31 open Assets:Cash

    2016-11-01 * "Foo" "Bar"
        statement: "asdf"
        Expenses:Foo                100 EUR
        Assets:Cash
    """
    entries, errors, _ = load_doc

    assert len(errors) == 1
    assert len(entries) == 3


def test_link_statements_missing(tmpdir):
    sample_folder = tmpdir.mkdir('fava_plugins').mkdir('documents')

    bfile = dedent("""
        option "documents" "{}"
        plugin "fava.plugins.link_statements"

        2016-10-31 open Expenses:Foo
        2016-10-31 open Assets:Cash

        2016-11-01 * "Foo" "Bar"
            statement: "test/Foobar.pdf"
            Expenses:Foo                100 EUR
            Assets:Cash
    """.format(sample_folder))

    entries, errors, _ = load_string(bfile)

    assert len(errors) == 1
    assert isinstance(errors[0], StatementDocumentError)
    assert len(entries) == 3
