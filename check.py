import sys
import classes.globals as g


if len(sys.argv) > 1:
    check_type = sys.argv[1]
    if check_type == "quotas":
        g.app.check_quotas()
        
    elif check_type == "preferences":
        if len(sys.argv) > 2:
            origin = sys.argv[2]
        g.app.check_preferences(origin)
        
    elif check_type == "pharma":
        g.app.check_pharma()
        
    elif check_type == "classification":
        if len(sys.argv) > 2:
            do_from = int(sys.argv[2])
        else:
            do_from = 1
        if len(sys.argv) > 3:
            do_to = int(sys.argv[3])
        else:
            do_to = 99
        g.app.check_classification(do_from, do_to)
    elif check_type == "class_report":
        g.app.write_classification_report()