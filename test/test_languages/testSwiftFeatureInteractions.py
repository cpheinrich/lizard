"""Swift reader features together in one compiler-valid file.

Computed and closure-initialized properties, enum case declarations,
condition-list commas and string interpolation each have their own tests.
This file checks them side by side, where one feature's tokens flow
through the others' scanners. The source passes `swiftc -typecheck`.
"""
import unittest
from lizard import FileAnalyzer, get_extensions


SOURCE = r'''let flag = true

struct V {
    var score:
        Int { if flag { return 1 }; return 0 }
    var label: String {
        "v \(flag ? "on" : "off") \(1 /* ) */ + (flag ? 2 : 3))"
    }
    let handler: (Int) -> Int = { x in
        if x > 0 { return 1 }
        return 0
    }
    var stored = 0 {
        didSet { if stored > 1 { print(stored) } }
    }
    enum Kind { case a, b
        case c }
    func check(_ a: Bool, _ b: Bool, _ xs: [Int]) -> Bool {
        guard a, b, xs.contains(where: { $0 > 1 }) else { return false }
        if "\(xs.map { $0 > 1 ? 1 : 0 })".isEmpty, a { return true }
        switch Kind.a { case .a: return true
        default: return false }
    }
}
'''


class TestSwiftFeatureInteractions(unittest.TestCase):

    def test_functions_and_global_scope(self):
        result = FileAnalyzer(get_extensions(["outside"])) \
            .analyze_source_code("a.swift", SOURCE)
        self.assertEqual([
            ("score", 4, 5, 2, 2),
            ("label", 6, 8, 3, 3),
            ("handler", 9, 12, 2, 4),
            ("didSet", 14, 14, 2, 1),
            # guard + 2 commas, if + ternary in the interpolated closure +
            # the comma after it, one switch case
            ("check", 18, 23, 8, 6),
            # enum cases and property bodies stay out of the global scope
            ("*global*", 0, 24, 1, 13),
        ], [(f.name, f.start_line, f.end_line, f.cyclomatic_complexity,
             f.nloc) for f in result.function_list])
        self.assertEqual(23, result.nloc)
