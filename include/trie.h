#ifndef INCLUDED_TRIE_H
#define INCLUDED_TRIE_H

#include "debug.h"

template <class T>
struct Trie {
    struct Node {
        map<typename T::value_type, Node*> chds;
        Node(): chds() {}
    };
    Node root;
    
    Trie() : root() {}
    
    void insert(const T& s) {
        Node* cur = &root;
        for (const auto& c : s) {
            if (!cur->chds.contains(c)) {
                cur->chds[c] = new Node();
            }
            cur = cur->chds[c];
        }
    }

    auto contains(const T& s) {
        Node* cur = &root;
        for (const auto& c : s) {
            if (!cur->chds.contains(c)) {
                return false;
            }
            cur = cur->chds[c];
        }
        return true;
    }

    auto closest(const T& s) {
        vector<T> results;
        T result;
        _closest(&root, s.begin(), s.end(), result, results);
        return results;
    }
    
    void _closest(Node* cur, typename T::const_iterator begin, typename T::const_iterator end, T& result, vector<T>& results) {
        if (begin == end) {
            results.push_back(result);
            return;
        }
        const auto& c = *begin;
        if (cur->chds.contains(c)) {
            result.push_back(c);
            _closest(cur->chds[c], begin + 1, end, result, results);
            result.pop_back();
        } else {
            if (cur->chds.size() > 0) {
                for (const auto& [c, chd] : cur->chds) {
                    result.push_back(c);
                    _closest(chd, begin + 1, end, result, results);
                    result.pop_back();
                }
            } else {
                results.push_back(result);
            }
        }
    }
};

#endif
