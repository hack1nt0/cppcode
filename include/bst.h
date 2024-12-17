#ifndef INCLUDED_BST_H
#define INCLUDED_BST_H
#include "debug.h"
#include <cassert>
#include <functional>
#include <iostream>
#include <unordered_map>
#include <vector>

/*
    struct Node {
        Node *chds[2];
        void maintain();
        Node(): chds({nullptr, nullptr}) {}
    }
*/
template <typename T> struct BaseBst {
    T *dummy, *root;
    BaseBst() : dummy(new T()), root(dummy) {}

    // T *rotate(T *root, int c = 2) { return root; }

    T *rotate(T *root, int c = 2) {
        int hl = root->chd[0]->height, hr = root->chd[1]->height;
        if (hl == hr || c == 0 || abs(hl - hr) < c)
            return root;
        T *ret;
        if (hl > hr) {
            if (root->chd[0]->chd[0]->height < root->chd[0]->chd[1]->height)
                root->chd[0] = this->rotate(root->chd[0], c - 1);
            ret = root->chd[0];
            T *tmp = root->chd[0]->chd[1];
            ret->chd[1] = root;
            ret->chd[1]->chd[0] = tmp;
        } else {
            if (root->chd[1]->chd[0]->height > root->chd[1]->chd[1]->height)
                root->chd[1] = this->rotate(root->chd[1], c - 1);
            ret = root->chd[1];
            T *tmp = root->chd[1]->chd[0];
            ret->chd[0] = root;
            ret->chd[0]->chd[1] = tmp;
        }
        return ret;
    }

    void insert(const T &v) { root = insert(v, root); }

    T *insert(const T &val, T *root) {
        T *ret;
        if (root == dummy) {
            ret = new T(val); //TODO
            // cerr << val.val << " == " << val.sum << endl;
            // *ret = val;
            ret->chd[0] = dummy;
            ret->chd[1] = dummy;
            ret->count = 1;
            ret->height = 1;
            ret->maintain();
        } else {
            ret = root;
            int cmp = val <=> *ret;
            if (cmp == 0) {
                ret->count++;
            } else if (cmp < 0) {
                ret->chd[0] = this->insert(val, ret->chd[0]);
            } else {
                ret->chd[1] = this->insert(val, ret->chd[1]);
            }
            ret->maintain();
            ret = this->rotate(ret);
            for (auto ptr : {ret->chd[0], ret->chd[1], ret})
                if (ptr != dummy) {
                    assert(ptr->chd[0] != nullptr && ptr->chd[1] != nullptr);
                    ptr->height = max(ptr->chd[0]->height, ptr->chd[1]->height) + 1;
                    ptr->maintain();
                }
        }
        return ret;
    }

    void erase(const T &node) { root = erase(node, root); }

    T *erase(const T &val, T *root) {
        if (root == dummy) {
            return root;
        }
        T *ret = root;
        int cmp = val <=> *root;
        if (cmp == 0) {
            root->count--;
            if (root->count > 0) {
                ret = root;
            } else if (root->chd[0] == dummy) {
                ret = root->chd[1];
                delete root;
            } else if (root->chd[0]->chd[1] == dummy) {
                ret = root->chd[0];
                ret->chd[1] = root->chd[1];
                delete root;
            } else {
                ret = root->chd[0];
                while (ret->chd[1] != dummy)
                    ret = ret->chd[1];
                ret = ret->fa;
                ret->fa->chd[1] = dummy;
                ret->chd[0] = root->chd[0];
                ret->chd[1] = root->chd[1];
                delete root;
            }
        } else if (cmp < 0) {
            root->chd[0] = this->erase(val, root->chd[0]);
            root->chd[0]->fa = root;
        } else {
            root->chd[1] = this->erase(val, root->chd[0]);
            root->chd[1]->fa = root;
        }
        ret = this->rotate(ret);
        ret->maintain();
        return ret;
    }

    void traverse(const function<bool(const T &root)> &preOrder,
                  const function<bool(const T &root)> &midOrder,
                  const function<void(const T &root)> &postOrder,
                  T *root = nullptr) const {
        if (root == nullptr) {
            root = this->root;
        }
        if (root == dummy)
            return;
        if (!preOrder(*root)) return;
        traverse(preOrder, midOrder, postOrder, root->chd[0]);
        if (!midOrder(*root)) return;
        traverse(preOrder, midOrder, postOrder, root->chd[1]);
        postOrder(*root);
    }

#ifdef DEBUG

    void dot() {
        cerr << "\ndigraph {\n";
        if (root != dummy) {
            int idx = 1;
            idx = _dot(root, idx);
            cerr << "{rank=source;" << idx << "}\n";
        }
        cerr << "}\n";
    }

    int _dot(T *root, int &idx) {
        if (root == dummy)
            return 0;
        int c, l, r;
        c = l = r = 0;
        l = _dot(root->chd[0], idx);
        c = idx++;
        cerr << '\t' << c << " [label=<" << *root << "<BR/>"
             << "height=" << root->height << "<BR/>"
             << ">]\n";
        r = _dot(root->chd[1], idx);
        if (l)
            cerr << '\t' << c << " -> " << l << "\n";
        if (r)
            cerr << '\t' << c << " -> " << r << "\n";
        return c;
    }
#endif
};

#endif